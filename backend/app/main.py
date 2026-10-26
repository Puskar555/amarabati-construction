"""Ammarabati v0.1 API. No real payments, no certified plans, no invented prices."""
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from threading import Lock

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .db import connection, one, all_rows
from .models import Register, Login, Consent, Event, OrderRequest, Project, RateProposal, NewProduct
from .security import hash_password, verify_password, token_hash, verify_totp, decrypt_secret, clean_event, can_access_region
from .costs import plot_preview

app = FastAPI(title='Ammarabati Local API', version='0.1.0', docs_url=None, redoc_url=None, openapi_url=None)
logger = logging.getLogger('amarabati.api')
logging.basicConfig(level=os.getenv('LOG_LEVEL','INFO'),format='%(asctime)s %(levelname)s %(message)s')
IS_PROD = os.getenv('APP_ENV','local') == 'production'
SIGNING_KEY = os.environ.get('APP_SIGNING_KEY','')
TOTP_KEY = os.environ.get('TOTP_ENCRYPTION_KEY','')
COOKIE_SECURE = os.getenv('COOKIE_SECURE','false').lower() == 'true'
ALLOWED_ORIGINS = {x.strip() for x in os.getenv('ALLOWED_ORIGINS','http://localhost:3000,http://localhost:3001,http://localhost:3002').split(',') if x.strip()}
if IS_PROD and (len(SIGNING_KEY)<40 or len(TOTP_KEY)<30 or not COOKIE_SECURE):
    raise RuntimeError('Production requires long signing key, TOTP encryption key, secure cookies')
if not SIGNING_KEY: SIGNING_KEY=secrets.token_hex(32)  # local only; consent tokens expire when restarted

_window = defaultdict(deque)
_window_lock = Lock()
def throttle(request: Request, scope: str, limit: int, window: int = 60):
    # In-process guard only. Add edge limiting / distributed rate limiter before production multi-node.
    # X-Real-IP is set by our private Nginx proxy (not client-supplied in public endpoints).
    client = request.headers.get('x-real-ip') or (request.client.host if request.client else 'unknown')
    key = (scope, client)
    now = time.monotonic()
    with _window_lock:
        series = _window[key]
        while series and series[0] < now-window: series.popleft()
        if len(series) >= limit: raise HTTPException(429, 'Too many requests. Try again later.')
        series.append(now)

def jresponse(row):
    return json.loads(json.dumps(row, default=lambda x: float(x) if isinstance(x,Decimal) else x.isoformat() if isinstance(x,datetime) else str(x)))

def sign(data: str) -> str:
    return hmac.new(SIGNING_KEY.encode(),data.encode(),hashlib.sha256).hexdigest()

def consent_status(request: Request):
    raw=request.cookies.get('ab_consent','')
    try:
        typ, visitor, sig=raw.split(':')
        if typ not in ('a','n') or not hmac.compare_digest(sign(f'{typ}:{visitor}'),sig): return None,None
        return typ=='a', visitor if typ=='a' else None
    except ValueError: return None,None

class GuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        rid=str(uuid.uuid4())
        if request.method in ('POST','PATCH','PUT','DELETE'):
            origin=request.headers.get('origin')
            if origin and origin not in ALLOWED_ORIGINS:
                return JSONResponse({'detail':'Origin not allowed','request_id':rid},status_code=403)
            if request.headers.get('sec-fetch-site') == 'cross-site':
                return JSONResponse({'detail':'Cross-site request rejected','request_id':rid},status_code=403)
        try:
            response=await call_next(request)
        except Exception:
            logger.exception('Unhandled exception request_id=%s path=%s',rid,request.url.path)
            response=JSONResponse({'detail':'Server error','request_id':rid},status_code=500)
        response.headers['X-Request-ID']=rid
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
        response.headers['Cache-Control']='no-store'
        return response
app.add_middleware(GuardMiddleware)

@app.get('/api/health')
def health():
    try:
        with connection() as db: one(db,'SELECT 1 AS ok')
        return {'status':'ok','database':'postgresql'}
    except Exception:
        raise HTTPException(503,'PostgreSQL unavailable')

def session_actor(request:Request):
    token=request.cookies.get('ab_sid','')
    if not token: return None
    with connection() as db:
        return one(db,"""SELECT u.id,u.name,u.email,u.role,u.region,s.csrf_hash
            FROM sessions s JOIN users u ON u.id=s.user_id
            WHERE s.token_hash=%s AND s.revoked_at IS NULL AND s.expires_at>now()""", (token_hash(token),))

def require_user(request:Request):
    actor=session_actor(request)
    if not actor: raise HTTPException(401,'Sign in required')
    return actor

def require_admin(request:Request):
    actor=require_user(request)
    if actor['role'] not in ('super_admin','regional_admin'): raise HTTPException(403,'Administrator access required')
    return actor

def super_only(request:Request):
    actor=require_admin(request)
    if actor['role']!='super_admin':raise HTTPException(403,'Super Admin required')
    return actor

def require_csrf(request:Request, actor=Depends(require_user)):
    header=request.headers.get('x-csrf-token','')
    cookie=request.cookies.get('ab_csrf','')
    if not header or not cookie or not hmac.compare_digest(header,cookie) or not hmac.compare_digest(token_hash(header),actor['csrf_hash']):
        raise HTTPException(403,'Invalid CSRF token')
    return actor

def admin_csrf(request:Request, actor=Depends(require_csrf)):
    if actor['role'] not in ('regional_admin','super_admin'):raise HTTPException(403,'Admin required')
    return actor

def audit(db, actor, action, subject_type, subject_id, info=None):
    db.execute('INSERT INTO audit_events(actor_id,action,subject_type,subject_id,info) VALUES(%s,%s,%s,%s,%s::jsonb)',
               (actor['id'] if actor else None,action,subject_type,str(subject_id),json.dumps(info or {})))

@app.get('/api/catalog')
def catalog(q:str='',category:str='',region:str='Kathmandu',limit:int=40):
    limit=max(1,min(80,limit))
    q=q.strip()[:90]
    with connection() as db:
        data=all_rows(db,"""SELECT p.id,p.slug,p.name,p.category,p.unit,p.description,p.specification,p.image_key,
            r.unit_rate,r.currency,r.approved_at AS price_updated_at
            FROM products p LEFT JOIN LATERAL (
              SELECT unit_rate,currency,approved_at FROM material_rates
              WHERE product_id=p.id AND status='approved' AND region IN (%s,'Nepal')
              ORDER BY (region=%s) DESC,approved_at DESC LIMIT 1
            ) r ON TRUE
            WHERE p.published AND (%s='' OR p.category=%s)
              AND (%s='' OR p.name ILIKE %s OR p.slug ILIKE %s OR p.specification ILIKE %s)
            ORDER BY p.id ASC LIMIT %s""",
            (region,region,category,category,q,'%'+q+'%','%'+q+'%','%'+q+'%',limit))
        categories=all_rows(db,'SELECT slug,name,description FROM categories ORDER BY name')
    return jresponse({'products':data,'categories':categories,'region':region})

@app.get('/api/products/{slug}')
def product(slug:str,region:str='Kathmandu'):
    with connection() as db:
        row=one(db,"""SELECT p.*,r.unit_rate,r.currency,r.approved_at AS price_updated_at FROM products p
          LEFT JOIN LATERAL (SELECT unit_rate,currency,approved_at FROM material_rates WHERE product_id=p.id
          AND status='approved' AND region IN (%s,'Nepal') ORDER BY (region=%s) DESC, approved_at DESC LIMIT 1) r ON TRUE
          WHERE p.slug=%s AND p.published""",(region,region,slug))
    if not row: raise HTTPException(404,'Product not found')
    return jresponse(row)

@app.post('/api/auth/register')
def register(body:Register,request:Request):
    throttle(request,'register',6,600)
    with connection() as db:
        if one(db,'SELECT id FROM users WHERE email=%s',(body.email,)):
            raise HTTPException(409,'This email already has an account')
        user=one(db,"""INSERT INTO users(name,email,password_hash,role,region)
            VALUES(%s,%s,%s,'customer',%s) RETURNING id,name,email,role,region""",
            (body.name.strip(),body.email,hash_password(body.password),body.region.strip()))
    return {'message':'Account created. Sign in to continue.','user':user}

@app.post('/api/auth/login')
def login(body:Login,response:Response,request:Request):
    throttle(request,'login',8,600)
    with connection() as db:
        user=one(db,'SELECT * FROM users WHERE email=%s',(body.email.strip().lower(),))
        if not user or not verify_password(body.password,user['password_hash']):
            raise HTTPException(401,'Incorrect email, password, or authentication code')
        if user['role'] != 'customer':
            if not user['totp_secret_enc'] or not TOTP_KEY:
                raise HTTPException(403,'Administrator MFA is not provisioned')
            try: secret=decrypt_secret(user['totp_secret_enc'],TOTP_KEY)
            except Exception: raise HTTPException(403,'Administrator MFA unavailable')
            if not verify_totp(secret,body.otp):raise HTTPException(401,'Incorrect email, password, or authentication code')
        token=secrets.token_urlsafe(48)
        csrf=secrets.token_urlsafe(32)
        db.execute("INSERT INTO sessions(token_hash,user_id,csrf_hash,expires_at) VALUES(%s,%s,%s,now()+interval '12 hours')",
                   (token_hash(token),user['id'],token_hash(csrf)))
        audit(db,user,'login','user',user['id'])
    response.set_cookie('ab_sid',token,httponly=True,secure=COOKIE_SECURE,samesite='lax',max_age=43200,path='/')
    response.set_cookie('ab_csrf',csrf,httponly=False,secure=COOKIE_SECURE,samesite='lax',max_age=43200,path='/')
    return {'user':{k:user[k] for k in ['id','name','email','role','region']}}

@app.get('/api/auth/me')
def me(request:Request):
    actor=session_actor(request)
    return {'user':({k:actor[k] for k in ['id','name','email','role','region']} if actor else None)}

@app.post('/api/auth/logout')
def logout(response:Response,request:Request,actor=Depends(require_csrf)):
    with connection() as db:
        db.execute('UPDATE sessions SET revoked_at=now() WHERE token_hash=%s',(token_hash(request.cookies.get('ab_sid','')),))
        audit(db,actor,'logout','user',actor['id'])
    response.delete_cookie('ab_sid',path='/')
    response.delete_cookie('ab_csrf',path='/')
    return {'ok':True}

@app.get('/api/consent')
def get_consent(request:Request):
    allowed,_=consent_status(request)
    return {'analytics':allowed,'choice_saved':allowed is not None}

@app.post('/api/consent')
def save_consent(body:Consent,response:Response,request:Request):
    allowed,existing_ref=consent_status(request)
    visitor_ref = existing_ref if body.analytics and existing_ref else str(uuid.uuid4()) if body.analytics else 'none'
    actor=session_actor(request)
    with connection() as db:
        if not body.analytics and existing_ref:
            db.execute('DELETE FROM activity_events WHERE visitor_ref=%s',(existing_ref,))
        db.execute('INSERT INTO consents(user_id,visitor_ref,analytics) VALUES(%s,%s,%s)',
                   (actor['id'] if actor else None,visitor_ref if body.analytics else None,body.analytics))
    kind='a' if body.analytics else 'n'
    response.set_cookie('ab_consent',f'{kind}:{visitor_ref}:{sign(f"{kind}:{visitor_ref}")}',secure=COOKIE_SECURE,
                        httponly=True,samesite='lax',max_age=60*60*24*180,path='/')
    return {'analytics':body.analytics,'choice_saved':True}

@app.post('/api/events')
def events(body:Event,request:Request):
    throttle(request,'events',100,60)
    allowed,visitor_ref=consent_status(request)
    if not allowed or not visitor_ref: return {'stored':False,'reason':'analytics_not_enabled'}
    try: details=clean_event(body.type,body.details)
    except ValueError as exc: raise HTTPException(422,str(exc))
    actor=session_actor(request)
    with connection() as db:
        db.execute("""INSERT INTO activity_events(event_id,visitor_ref,user_id,event_name,details,region)
           VALUES(%s,%s,%s,%s,%s::jsonb,%s) ON CONFLICT(event_id) DO NOTHING""",
           (body.event_id,visitor_ref,actor['id'] if actor else None,body.type,json.dumps(details),body.region))
    return {'stored':True}

@app.post('/api/orders')
def request_order(body:OrderRequest,request:Request,actor=Depends(require_csrf)):
    throttle(request,'orders',15,3600)
    if len({i.product_id for i in body.items}) != len(body.items):raise HTTPException(422,'Duplicate product lines')
    with connection() as db:
        lines=[]
        for item in body.items:
            prod=one(db,"""SELECT p.id,p.name,p.unit,r.unit_rate FROM products p
                LEFT JOIN LATERAL (SELECT unit_rate FROM material_rates WHERE product_id=p.id AND status='approved'
                AND region IN (%s,'Nepal') ORDER BY (region=%s) DESC,approved_at DESC LIMIT 1) r ON TRUE
                WHERE p.id=%s AND p.published""",(body.delivery_region,body.delivery_region,item.product_id))
            if not prod: raise HTTPException(422,f'Product #{item.product_id} unavailable')
            lines.append((prod,item.quantity))
        full_priced=all(p['unit_rate'] is not None for p,q in lines)
        status='awaiting_payment_integration' if full_priced else 'quote_requested'
        total=sum((Decimal(p['unit_rate'])*q for p,q in lines),Decimal('0')) if full_priced else None
        order=one(db,"""INSERT INTO orders(user_id,delivery_region,notes,status,total_amount)
            VALUES(%s,%s,%s,%s,%s) RETURNING id,status,created_at""",
            (actor['id'],body.delivery_region,body.notes,status,total))
        for p,q in lines:
            rate=p['unit_rate']
            db.execute("""INSERT INTO order_lines(order_id,product_id,quantity,unit_rate,product_name_snapshot,line_total)
                VALUES(%s,%s,%s,%s,%s,%s)""",(order['id'],p['id'],q,rate,p['name'],rate*q if rate is not None else None))
        audit(db,actor,'order_request','order',order['id'],{'status':status})
    return jresponse({'order':order,'total_amount':total,'message':'Order request saved. No payment was collected.'})

@app.get('/api/orders')
def my_orders(actor=Depends(require_user)):
    with connection() as db:
        rows=all_rows(db,'SELECT id,status,total_amount,currency,delivery_region,created_at FROM orders WHERE user_id=%s ORDER BY id DESC LIMIT 40',(actor['id'],))
    return jresponse({'orders':rows})

@app.post('/api/projects')
def save_project(body:Project,actor=Depends(require_csrf)):
    preview=plot_preview(body.width_m,body.depth_m)
    requirements=json.dumps({k:v for k,v in body.requirements.items() if k in ('rooms','parking','finish','road_side') and isinstance(v,(int,str,bool))})
    with connection() as db:
        row=one(db,"""INSERT INTO projects(user_id,title,project_type,municipality,width_m,depth_m,floors,requirements)
             VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb) RETURNING id,title,created_at""",
            (actor['id'],body.title,body.project_type,body.municipality,body.width_m,body.depth_m,body.floors,requirements))
        audit(db,actor,'project_created','project',row['id'])
    return {'project':jresponse(row),'preview':preview}

@app.get('/api/projects')
def my_projects(actor=Depends(require_user)):
    with connection() as db:
        rows=all_rows(db,'SELECT id,title,project_type,municipality,width_m,depth_m,floors,created_at FROM projects WHERE user_id=%s ORDER BY id DESC LIMIT 40',(actor['id'],))
    return {'projects':jresponse(rows)}

@app.get('/api/admin/overview')
def overview(actor=Depends(require_admin)):
    regional=actor['role']=='regional_admin'
    reg=actor['region'] or ''
    with connection() as db:
        if regional:
            order_count=one(db,'SELECT count(*) AS count FROM orders WHERE delivery_region=%s',(reg,))['count']
            project_count=one(db,'SELECT count(*) AS count FROM projects WHERE municipality=%s',(reg,))['count']
            event_count=one(db,'SELECT count(*) AS count FROM activity_events WHERE region=%s',(reg,))['count']
            quotes=all_rows(db,"SELECT id,delivery_region,status,created_at FROM orders WHERE delivery_region=%s ORDER BY id DESC LIMIT 15",(reg,))
            events=all_rows(db,'SELECT event_name,count(*) AS total FROM activity_events WHERE region=%s GROUP BY event_name ORDER BY total DESC LIMIT 8',(reg,))
        else:
            order_count=one(db,'SELECT count(*) AS count FROM orders')['count']
            project_count=one(db,'SELECT count(*) AS count FROM projects')['count']
            event_count=one(db,'SELECT count(*) AS count FROM activity_events')['count']
            quotes=all_rows(db,'SELECT id,delivery_region,status,created_at FROM orders ORDER BY id DESC LIMIT 15')
            events=all_rows(db,'SELECT event_name,count(*) AS total FROM activity_events GROUP BY event_name ORDER BY total DESC LIMIT 8')
    return jresponse({'role':actor['role'],'region':reg,'order_count':order_count,'project_count':project_count,'event_count':event_count,'orders':quotes,'events':events})

@app.get('/api/admin/rates')
def rate_list(actor=Depends(require_admin)):
    with connection() as db:
        if actor['role']=='super_admin':
            rows=all_rows(db,"""SELECT r.id,p.name AS product_name,r.product_id,r.region,r.currency,r.unit_rate,r.status,r.note,
                r.proposed_at,r.approved_at FROM material_rates r JOIN products p ON p.id=r.product_id
                ORDER BY r.id DESC LIMIT 150""")
        else:
            rows=all_rows(db,"""SELECT r.id,p.name AS product_name,r.product_id,r.region,r.currency,r.unit_rate,r.status,r.note,
                r.proposed_at,r.approved_at FROM material_rates r JOIN products p ON p.id=r.product_id
                WHERE r.region=%s ORDER BY r.id DESC LIMIT 150""",(actor['region'],))
    return {'rates':jresponse(rows)}

@app.post('/api/admin/rates')
def propose_rate(body:RateProposal,actor=Depends(admin_csrf)):
    if not can_access_region(actor['role'],actor['region'],body.region):raise HTTPException(403,'Region outside your assignment')
    with connection() as db:
        if not one(db,'SELECT id FROM products WHERE id=%s',(body.product_id,)):raise HTTPException(404,'Unknown product')
        row=one(db,"""INSERT INTO material_rates(product_id,region,currency,unit_rate,note,proposed_by)
             VALUES(%s,%s,%s,%s,%s,%s) RETURNING id,status""",
            (body.product_id,body.region,body.currency,Decimal(str(body.unit_rate)),body.note,actor['id']))
        audit(db,actor,'rate_proposed','material_rate',row['id'],{'region':body.region})
    return {'rate':row}

@app.post('/api/admin/rates/{rate_id}/approve')
def approve_rate(rate_id:int,actor=Depends(require_csrf)):
    if actor['role']!='super_admin':raise HTTPException(403,'Super Admin approval required')
    with connection() as db:
        rate=one(db,'SELECT id,status,proposed_by FROM material_rates WHERE id=%s FOR UPDATE',(rate_id,))
        if not rate:raise HTTPException(404,'Rate not found')
        if rate['status']!='pending':raise HTTPException(409,'Rate already reviewed')
        if rate['proposed_by']==actor['id']:raise HTTPException(403,'A second administrator must approve this rate')
        db.execute("UPDATE material_rates SET status='approved',approved_by=%s,approved_at=now() WHERE id=%s",(actor['id'],rate_id))
        audit(db,actor,'rate_approved','material_rate',rate_id)
    return {'approved':True}

@app.post('/api/admin/products')
def add_product(body:NewProduct,actor=Depends(require_csrf)):
    if actor['role']!='super_admin':raise HTTPException(403,'Super Admin required')
    with connection() as db:
        if not one(db,'SELECT slug FROM categories WHERE slug=%s',(body.category,)):raise HTTPException(422,'Unknown category')
        if one(db,'SELECT id FROM products WHERE slug=%s',(body.slug,)):raise HTTPException(409,'Slug already used')
        row=one(db,"""INSERT INTO products(slug,name,category,unit,description,specification)
            VALUES(%s,%s,%s,%s,%s,%s) RETURNING id,name""",
            (body.slug,body.name,body.category,body.unit,body.description,body.specification))
        audit(db,actor,'product_created','product',row['id'])
    return {'product':row}

@app.get('/api/admin/audit')
def audit_logs(actor=Depends(super_only)):
    with connection() as db:
        rows=all_rows(db,"""SELECT id,actor_id,action,subject_type,subject_id,created_at
            FROM audit_events ORDER BY id DESC LIMIT 100""")
    return {'events':jresponse(rows)}
