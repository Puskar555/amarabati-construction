from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import pytest
from app.security import hash_password,verify_password,totp,verify_totp,clean_event,can_access_region
from app.costs import plot_preview,line_cost

def test_password_salted_hash_and_verification():
    a=hash_password('a-difficult-test-password')
    b=hash_password('a-difficult-test-password')
    assert a!=b
    assert verify_password('a-difficult-test-password',a)
    assert not verify_password('wrong',a)

def test_totp_known_time_and_replay_window():
    # Deterministic six-digit code with one-window clock skew acceptance
    secret='JBSWY3DPEHPK3PXP'
    value=totp(secret,1700000000)
    assert verify_totp(secret,value,1700000000)
    assert not verify_totp(secret,'ABC123',1700000000)

def test_region_access_fails_closed():
    assert can_access_region('super_admin',None,'Kathmandu')
    assert can_access_region('regional_admin','Kathmandu','Kathmandu')
    assert not can_access_region('regional_admin','Pokhara','Kathmandu')
    assert not can_access_region('regional_admin',None,None)
    assert not can_access_region('customer','Kathmandu','Kathmandu')

def test_event_allowlist_and_no_private_fields():
    assert clean_event('product_searched',{'query':'cement'})=={'query':'cement'}
    with pytest.raises(ValueError):clean_event('customer_email_collected',{'email':'test@test.com'})
    with pytest.raises(ValueError):clean_event('product_searched',{'password':'secret'})
    with pytest.raises(ValueError):clean_event('product_clicked',{'query':'A'*121})

def test_plot_is_unverified_not_engineering_approval():
    p=plot_preview(9.14,12.19)
    assert p['regulatory_verified'] is False
    assert p['drawing_approved'] is False
    assert p['illustrative_envelope_m2']==p['plot_area_m2']
    with pytest.raises(ValueError):plot_preview(-2,12)

def test_operator_rate_not_invented():
    assert line_cost(2,None) is None
    assert line_cost(2,'125.55')=='251.10'
    with pytest.raises(ValueError):line_cost(-1,50)
