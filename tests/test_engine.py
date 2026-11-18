from app.engine import evaluate, valid_barcode

BASE='Product name: Tea\nManufactured by: Acme, Pune\nNet quantity: 500 g\nDate of packing: 08/2026\nMRP Rs. 20 incl. of all taxes\nConsumer care: 12345678'
def test_complete_text_passes_required_fields():
    result=evaluate(BASE); assert all(x['status']=='PASS' for x in result['results'] if x['id']!='LM-TODO-08' and x['id']!='LM-TODO-09')
def test_score_bounds():
    r=evaluate(BASE); assert 0<=r['score']<=100
def test_unverified_flag(): assert evaluate(BASE)['has_unverified_rules']
def test_missing_manufacturer_fails(): assert next(x for x in evaluate(BASE.replace('Manufactured by: Acme, Pune\n',''))['results'] if x['id']=='LM-TODO-01')['status']=='FAIL'
def test_import_country_conditional(): assert next(x for x in evaluate(BASE+'\nImported by: Acme')['results'] if x['id']=='LM-TODO-07')['status']=='FAIL'
def test_height_review_without_width(): assert next(x for x in evaluate(BASE)['results'] if x['id']=='LM-TODO-08')['status']=='NEEDS_REVIEW'
def test_valid_ean13(): assert valid_barcode('4006381333931')
def test_invalid_ean13(): assert not valid_barcode('4006381333932')
def test_unknown_barcode_invalid(): assert not valid_barcode('abc')
def test_missing_mrp_fails(): assert next(x for x in evaluate(BASE.replace('MRP Rs. 20 incl. of all taxes\n',''))['results'] if x['id']=='LM-TODO-05')['status']=='FAIL'
