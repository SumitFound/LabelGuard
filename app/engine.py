from .extract import extract_fields
import json
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parents[1] / 'rules' / 'rules.json'
def load_rules(): return json.loads(RULES_PATH.read_text(encoding='utf-8'))

def valid_barcode(value):
    digits = ''.join(c for c in str(value or '') if c.isdigit())
    if len(digits) == 13:
        n = sum(int(d) * (1 if i % 2 == 0 else 3) for i,d in enumerate(digits[:12]))
        return (10 - n % 10) % 10 == int(digits[-1])
    if len(digits) == 12:
        n = sum(int(d) * (3 if i % 2 == 0 else 1) for i,d in enumerate(digits[:11]))
        return (10 - n % 10) % 10 == int(digits[-1])
    return False

def evaluate(text, ocr_items=None, package_width_mm=None, image_width_px=None, barcode=None, rules=None):
    rules = rules or load_rules(); fields = extract_fields(text); out=[]
    for rule in rules:
        key, check = rule['field'], rule['check']; value = barcode if key == 'barcode' else fields.get(key); expected=None; bbox=None
        if check == 'present': ok=bool(value)
        elif check == 'quantity': ok=bool(value and value.lower().split()[-1].rstrip('s') in rule['params']['units']); expected=rule['params']['units']
        elif check == 'mrp_inclusive': ok=fields.get('mrp_inclusive',False); expected='inclusive of all taxes'
        elif check == 'conditional_origin': ok=not fields.get('suggests_import') or bool(fields.get('country_origin')); expected='country of origin if import suggested'
        elif check == 'height':
            expected='minimum TODO verify against official gazette'
            ok=None
            if package_width_mm and image_width_px and ocr_items:
                item=next((x for x in ocr_items if value and value in x.get('text','')),None)
                if item:
                    bbox=item.get('bbox'); ys=[p[1] for p in bbox] if bbox and isinstance(bbox[0],(list,tuple)) else []
                    if ys: _height_mm=(max(ys)-min(ys))*package_width_mm/image_width_px
        elif check == 'barcode': ok=valid_barcode(value); expected='valid EAN-13 or UPC'
        else: ok=None
        status='NEEDS_REVIEW' if ok is None else 'PASS' if ok else 'FAIL'
        explanation=rule['description'] if status=='PASS' else ('Required evidence is unavailable or the threshold needs verification.' if status=='NEEDS_REVIEW' else 'Required label information was not detected or did not satisfy this check.')
        out.append({'id':rule['id'],'status':status,'extracted':value,'expected':expected,'explanation':explanation,'reference':rule['reference'],'verified':rule['verified'],'bbox':bbox})
    weights={'high':3,'medium':2,'low':1}; total=sum(weights.get(r.get('severity','medium'),2) for r in rules)
    score=round(100*sum(weights.get(r.get('severity','medium'),2)*({'PASS':1,'NEEDS_REVIEW':.5,'FAIL':0}[o['status']]) for r,o in zip(rules,out))/total) if total else 0
    return {'results':out,'score':score,'verdict':'PASS' if score>=80 and all(x['status']!='FAIL' for x in out) else 'NEEDS_REVIEW' if any(x['status']=='NEEDS_REVIEW' for x in out) else 'FAIL','has_unverified_rules':any(not x['verified'] for x in out),'fields':fields}
