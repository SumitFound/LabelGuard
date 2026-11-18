from app.extract import extract_fields

def test_manufacturer(): assert 'Acme' in extract_fields('Manufactured by: Acme, Delhi')['manufacturer']
def test_generic_name(): assert extract_fields('Product name: Soap')['generic_name']=='Soap'
def test_quantity(): assert extract_fields('Net quantity: 250 ml')['net_quantity']=='250 ml'
def test_quantity_units(): assert extract_fields('500 g')['net_quantity']=='500 g'
def test_numeric_date(): assert extract_fields('Date of packing: 08/2026')['date']=='08/2026'
def test_month_date(): assert extract_fields('Packed: Aug 2026')['date']=='Aug 2026'
def test_mrp_inclusive(): assert extract_fields('MRP Rs. 10 inclusive of all taxes')['mrp_inclusive']
def test_mrp_missing_phrase(): assert not extract_fields('MRP Rs. 10')['mrp_inclusive']
def test_consumer_care(): assert 'help@' in extract_fields('Consumer care: help@example.in')['consumer_care']
def test_origin(): assert extract_fields('Country of origin: India')['country_origin']=='India'
