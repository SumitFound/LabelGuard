import cv2
import numpy as np
from PIL import Image
from io import BytesIO

def ocr(image):
    """Return OCR detections as (text, bbox, confidence); backend can be replaced here."""
    from rapidocr_onnxruntime import RapidOCR
    engine=RapidOCR(); result,_=engine(image)
    return [(row[1],row[0],float(row[2])) for row in (result or [])]

def decode_barcode(image):
    try:
        from pyzbar.pyzbar import decode
        found=decode(image)
        if found: return found[0].data.decode('utf-8','ignore')
    except Exception: pass
    try:
        value,_,_=cv2.QRCodeDetector().detectAndDecode(image)
        return value or None
    except Exception: return None

def process_image(data):
    try:
        pil=Image.open(BytesIO(data)).convert('RGB'); rgb=np.array(pil); gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    except Exception as exc: raise ValueError('Unable to read image. Upload a valid PNG or JPEG.') from exc
    variance=float(cv2.Laplacian(gray,cv2.CV_64F).var())
    if variance < 20: raise ValueError('Image is too blurry to inspect. Please upload a sharper, well-lit image.')
    # Deskew using the dominant text angle, then improve local contrast.
    coords=np.column_stack(np.where(gray<200))
    if len(coords)>20:
        angle=cv2.minAreaRect(coords.astype(np.float32))[-1]
        angle=-(90+angle) if angle < -45 else -angle
        if abs(angle)<15:
            h,w=gray.shape; matrix=cv2.getRotationMatrix2D((w/2,h/2),angle,1.0); gray=cv2.warpAffine(gray,matrix,(w,h),borderMode=cv2.BORDER_REPLICATE)
    enhanced=cv2.createCLAHE(clipLimit=2.0,tileGridSize=(8,8)).apply(gray)
    detections=ocr(enhanced)
    return enhanced, detections, decode_barcode(rgb), variance
