"""Optional static visual smoke test using Playwright; doesn't require PostgreSQL.
Run: pip install playwright; python scripts/visual_qa.py
Output: artifacts/ screenshots (not for public production screenshots).
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts'
OUT.mkdir(exist_ok=True)
store=ROOT/'apps/store/index.html'

def load_store(page):
    html=store.read_text().replace('<script type="module" src="/app.js"></script>','')
    css='\n'.join((ROOT/'apps/shared'/x).read_text() for x in ('base.css','utilities.css'))+(ROOT/'apps/store/store.css').read_text()
    client=(ROOT/'apps/shared/client.js').read_text().replace('export ','')
    app=(ROOT/'apps/store/app.js').read_text().split('\n',1)[1]
    # about:blank screenshot harness (network restricted in some build environments)
    app=app.replace("const route=()=>location.pathname.replace(/\\/$/,'')||'/';", "const route=()=>'/';")
    page.goto('about:blank')
    page.evaluate('''() => {const values={'ab_analytics_pref':'declined'}; Object.defineProperty(window,"localStorage",{configurable:true,value:{getItem:k=>values[k]||null,setItem:(k,v)=>{values[k]=v},removeItem:k=>{delete values[k]}}});}''')
    page.set_content(html)
    page.add_style_tag(content=css)
    page.add_script_tag(content=client+'\nconst e=escapeHTML;\n'+app)
    page.wait_for_timeout(350)
    assert page.locator('h1').count()>0
    assert page.locator('.product-card').count()==8

with sync_playwright() as p:
    for name,width,height in [('store-desktop',1440,900),('store-mobile',390,844)]:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':width,'height':height})
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        load_store(page)
        assert not errors,errors
        page.screenshot(path=str(OUT/f'{name}.png'),full_page=True)
        print(f'{name}: PASS, screenshot saved')
        browser.close()
