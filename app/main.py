import json, re
from pathlib import Path
from datetime import date
from collections import Counter
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
import cv2
import numpy as np
from .pipeline import process_image
from .engine import evaluate, load_rules
from .db import SessionLocal, Scan
from .report import make_report

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'annotated'; OUT.mkdir(exist_ok=True)
app=FastAPI(title='LabelGuard',description='Packaged commodity label screening; unverified rules need human review.')
app.mount('/files',StaticFiles(directory=OUT),name='files')
STATIC=ROOT/'static'; STATIC.mkdir(exist_ok=True)
app.mount('/static',StaticFiles(directory=STATIC),name='static')

@app.get('/')
def home(): return FileResponse(STATIC/'index.html')

@app.get('/api/samples')
def samples():
    folder=ROOT/'sample_images'
    return {'samples':[{'name':p.name,'url':f'/samples/{p.name}'} for p in sorted(folder.glob('*.png'))]}

app.mount('/samples',StaticFiles(directory=ROOT/'sample_images'),name='samples')
@app.post('/api/scan')
async def scan(image: UploadFile=File(...), package_width_mm: float|None=Form(None)):
    data=await image.read()
    if not data: raise HTTPException(400,'Empty image file.')
    if len(data)>20*1024*1024: raise HTTPException(413,'Image exceeds 20 MB limit.')
    try: processed,dets,barcode,variance=process_image(data)
    except ValueError as exc: raise HTTPException(400,str(exc))
    except Exception as exc: raise HTTPException(422,'Image could not be processed. Please try a PNG or JPEG.') from exc
    text='\n'.join(x[0] for x in dets)
    if not text.strip(): raise HTTPException(422,'No readable text found. Try a sharper image with better lighting.')
    h,w=processed.shape; items=[{'text':t,'bbox':b,'conf':c} for t,b,c in dets]
    result=evaluate(text,items,package_width_mm,w,barcode)
    rgb=cv2.cvtColor(processed,cv2.COLOR_GRAY2BGR)
    for det in dets:
        label=det[0].lower()
        matched=next((r for r in result['results'] if r['extracted'] and str(r['extracted']).lower() in label),None)
        color=(0,180,0) if matched and matched['status']=='PASS' else (0,0,230) if matched and matched['status']=='FAIL' else (0,180,220)
        pts=np.array(det[1],dtype=np.int32).reshape((-1,1,2)); cv2.polylines(rgb,[pts],True,color,2)
    name=f'scan-{__import__("uuid").uuid4().hex}.jpg'; cv2.imwrite(str(OUT/name),rgb); url=f'/files/{name}'
    session=SessionLocal()
    record=Scan(filename=image.filename or 'upload',score=result['score'],verdict=result['verdict'],result_json=json.dumps(result),image_url=url)
    session.add(record); session.commit(); session.refresh(record); record_id=record.id; session.close()
    return {'id':record_id,**result,'image_url':url,'quality':{'laplacian_variance':round(variance,2)},'ocr_text':text,'barcode':barcode}

@app.get('/api/history')
def history():
    s=SessionLocal(); rows=s.query(Scan).order_by(Scan.created_at.desc()).limit(100).all(); out=[{'id':r.id,'created_at':r.created_at.isoformat(),'filename':r.filename,'score':r.score,'verdict':r.verdict,'image_url':r.image_url} for r in rows]; s.close(); return out
@app.get('/api/scan/{scan_id}')
def scan_detail(scan_id:int):
    s=SessionLocal(); r=s.get(Scan,scan_id)
    if not r: s.close(); raise HTTPException(404,'Scan not found.')
    data=json.loads(r.result_json); data.update({'id':r.id,'image_url':r.image_url,'created_at':r.created_at.isoformat(),'filename':r.filename}); s.close(); return data
@app.get('/api/stats')
def stats():
    s=SessionLocal(); rows=s.query(Scan).all(); s.close(); failed=Counter(); days=Counter(); counts=Counter()
    for r in rows:
        counts[r.verdict]+=1; days[r.created_at.date().isoformat()]+=1
        for item in json.loads(r.result_json)['results']:
            if item['status']=='FAIL': failed[item['id']]+=1
    return {'pass_count':counts['PASS'],'fail_count':counts['FAIL'],'needs_review_count':counts['NEEDS_REVIEW'],'top_failed_rules':[{'id':k,'count':v} for k,v in failed.most_common(5)],'scans_per_day':dict(sorted(days.items()))}
@app.get('/api/report/{scan_id}')
def report(scan_id:int):
    s=SessionLocal(); record=s.get(Scan,scan_id); s.close()
    if not record: raise HTTPException(404,'Scan not found.')
    return Response(make_report(record),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename=labelguard-{scan_id}.pdf'})
class Question(BaseModel): question:str
@app.post('/api/ask')
def ask(body:Question):
    terms=set(re.findall(r'[a-z0-9]+',body.question.lower())); scored=[]
    for rule in load_rules():
        hay=' '.join([rule['id'],rule['description'],rule['field'],rule['reference']]).lower(); score=sum(1 for t in terms if t in hay)
        if score: scored.append((score,rule))
    return {'matches':[{'id':r['id'],'description':r['description'],'reference':r['reference'],'verified':r['verified'],'match_score':n} for n,r in sorted(scored,key=lambda x:x[0],reverse=True)[:5]]}
