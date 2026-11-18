import re

def extract_fields(text):
    t = text or ""
    patterns = {
        "manufacturer": r"(?im)(?:manufactured|packed|imported)\s+by\s*[:\-]?\s*([^\n]+)",
        "generic_name": r"(?im)(?:product|common|generic)\s*(?:name)?\s*[:\-]\s*([^\n]+)",
        "net_quantity": r"(?i)(?:net\s*(?:qty|quantity|weight|contents?)\s*[:\-]?\s*)?(\d+(?:\.\d+)?)\s*(kg|mg|ml|cl|g|l|nos?)\b",
        "date": r"(?i)(?:(?:manufacture|manufacturing|packing|packed|import)\w*\s*(?:date)?\s*[:\-]?\s*)?(\b(?:0?[1-9]|1[0-2])[/\-.](?:19|20)?\d{2}\b|\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(?:19|20)?\d{2}\b)",
        "mrp": r"(?i)(?:mrp|maximum\s+retail\s+price)\s*[:\-]?\s*(?:rs\.?|₹)?\s*\d+(?:\.\d{1,2})?[^\n]*",
        "consumer_care": r"(?i)(?:consumer\s+care|customer\s+care|helpline|contact)\s*[:\-]?\s*[^\n]+",
        "country_origin": r"(?i)(?:country\s+of\s+origin|made\s+in)\s*[:\-]?\s*([A-Za-z ]+)",
    }
    result = {}
    for key, pattern in patterns.items():
        m = re.search(pattern, t)
        if m:
            result[key] = (f'{m.group(1)} {m.group(2)}' if key == 'net_quantity' else (m.group(1) if m.lastindex else m.group(0))).strip()
    result["mrp_inclusive"] = bool(result.get("mrp") and re.search(r"(?i)inclusive\s+of\s+all\s+taxes|incl\.?\s+of\s+all\s+taxes", result["mrp"]))
    result["suggests_import"] = bool(re.search(r"(?i)import(?:ed)?\s+by|country\s+of\s+origin", t))
    return result
