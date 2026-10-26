from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
def test_private_database_and_csp():
    compose=(BASE/'compose.yaml').read_text()
    assert '127.0.0.1:5433:5432' in compose
    assert 'postgres:17-alpine' in compose
    assert 'no-new-privileges:true' in compose
    conf=(BASE/'deploy/nginx/site.conf').read_text()
    assert 'Content-Security-Policy' in conf
    assert "frame-ancestors 'none'" in conf

def test_no_unapproved_prices_in_seed():
    text=(BASE/'db/seed.sql').read_text()
    assert 'INSERT INTO material_rates' not in text

def test_admin_frontends_are_independent():
    for site in ('store','super','regional'):
        assert (BASE/'apps'/site/'index.html').exists()
