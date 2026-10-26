import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_anonymous_session_and_admin_denied():
    assert client.get('/api/auth/me').json()['user'] is None
    assert client.get('/api/admin/overview').status_code == 401
    assert client.post('/api/admin/rates',json={}).status_code in (401,422)

def test_reject_cross_site_mutations():
    r=client.post('/api/consent',json={'analytics':True},headers={'Origin':'https://attacker.example'})
    assert r.status_code==403
    assert r.json()['detail']=='Origin not allowed'
    r2=client.post('/api/consent',json={'analytics':True},headers={'Sec-Fetch-Site':'cross-site'})
    assert r2.status_code==403

def test_security_headers_and_request_id():
    response=client.get('/api/auth/me')
    assert response.headers['X-Frame-Options']=='DENY'
    assert response.headers['X-Content-Type-Options']=='nosniff'
    assert response.headers.get('X-Request-ID')
