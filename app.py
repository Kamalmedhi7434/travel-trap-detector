"""Local Flask server. Open http://127.0.0.1:5000. No cloud services."""
from pathlib import Path
from datetime import datetime, timezone
import sqlite3, json, uuid, math, base64, io, os
from flask import Flask, request, jsonify, send_from_directory, send_file
from train import CITIES, SERVICES
from ml import Models
ROOT=Path(__file__).resolve().parent
app=Flask(__name__,static_folder=None)
app.config['MAX_CONTENT_LENGTH']=30*1024*1024
app.json.ensure_ascii=False
DB=Path(os.environ.get('TRAVEL_DB',str(ROOT/'data/travel.db')))
AREAS={'guwahati':['City centre','Station area','Temple approach','Riverfront'],'jaipur':['City centre','Station area','Old city','Fort approach'],'delhi':['City centre','Station area','Market area','Monument approach'],'agra':['City centre','Station area','Monument approach','Market area'],'varanasi':['City centre','Station area','Ghat approach','Market area'],'goa':['City centre','Bus stand area','Beach approach','Market area'],'shillong':['City centre','Taxi stand area','Viewpoint approach','Market area'],'kolkata':['City centre','Station area','Market area','Riverfront']}
DB.parent.mkdir(exist_ok=True)

def connect():
    db=sqlite3.connect(DB);db.row_factory=sqlite3.Row;return db
with connect() as db:
    db.executescript('CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, data TEXT NOT NULL); CREATE TABLE IF NOT EXISTS checks (id TEXT PRIMARY KEY, data TEXT NOT NULL); CREATE TABLE IF NOT EXISTS evidence (id TEXT PRIMARY KEY, name TEXT, type TEXT, body BLOB);')
if not (ROOT/'models/fare.joblib').exists():
    from train import train
    train()
models=Models()

def rows(table):
    with connect() as db:return [json.loads(r['data']) for r in db.execute('SELECT data FROM '+table)]
def number(value,label,maximum):
    try:n=float(value)
    except (ValueError,TypeError):raise ValueError(label+' must be a number.')
    if not math.isfinite(n) or n<=0 or n>maximum:raise ValueError(label+' is outside the allowed range.')
    return n

def check_input(v):
    if not isinstance(v,dict):raise ValueError('Expected an object.')
    if v.get('city') not in CITIES or v.get('service') not in SERVICES:raise ValueError('Choose a supported city and service.')
    if v.get('area') not in AREAS[v['city']]:raise ValueError('Choose a supported area.')
    if v.get('time') not in ['day','night']:raise ValueError('Choose day or night.')
    v={k:v.get(k) for k in ['city','service','area','time','amount','quote','flags']}
    v['amount']=number(v['amount'],'Quantity',1000);v['quote']=number(v['quote'],'Quote',1000000)
    if not isinstance(v['flags'],list) or any(f not in ['extras','pressure','diversion','receipt'] for f in v['flags']):raise ValueError('Invalid situation warnings.')
    v['flags']=list(set(v['flags']));return v

def median(values):return float(__import__('numpy').median(values))
def analyze(v):
    v=check_input(v);now=datetime.now(timezone.utc).timestamp()
    reports=rows('reports');prediction=models.price(v['city'],v['service'],v['amount'],v['time'])
    samples=[];complaints=[]
    for r in reports:
        age=(now-datetime.fromisoformat(r['date']).replace(tzinfo=timezone.utc).timestamp())/86400
        if r['city']==v['city'] and r['service']==v['service'] and 0<=age<=365 and r['kind']=='fare' and r['time']==v['time'] and .5<=r['amount']/v['amount']<=2:
            samples.append(r['fare']*v['amount']/r['amount'])
        if r['city']==v['city'] and r['service']==v['service'] and r['area']==v['area'] and r['kind']=='complaint' and 0<=age<=180:complaints.append(r)
    kept=[]
    if samples:
        mid=median(samples);kept=[n for n in samples if .5*mid<=n<=1.8*mid]
    enough=len(kept)>=3
    # Blend local median with learned fare, rather than pretending local reports are verified.
    center=.7*median(kept)+.3*prediction if enough else prediction
    spread=max(.2,min(.45,2*median([abs(x-center) for x in kept])/center)) if enough else max(.25,models.metrics['fare_relative_error_90pct'])
    low=max(1,math.floor(center*(1-spread)/5)*5);high=math.ceil(center*(1+spread)/5)*5
    ratio=v['quote']/center;unusual=models.unusual(ratio);risk=models.classify(ratio,v['flags'],len(complaints),unusual['flag'])
    reasons=[]
    limit=40 if v['service'] in ['auto','taxi'] else 8
    if v['amount']<1 or v['amount']>limit:reasons.append('Quantity is outside the training range (1-'+str(limit)+'). This is extrapolation with lower reliability.')
    if v['quote']>high:reasons.append(f"Quote is {round((v['quote']/high-1)*100)}% above the estimated upper limit of ₹{high:,.0f}.")
    elif v['quote']<low*.5:reasons.append('Quote is unusually low. Check exclusions and inclusions before committing.')
    else:reasons.append('The quote is inside or below the working price range. This is not a safety guarantee.')
    texts={'extras':'Extra charges are unclear: ask for an all-in total.','pressure':'Payment pressure was reported: take time to check the service.','diversion':'An unrequested detour or change of destination was reported.','receipt':'A written price or receipt was reportedly refused.'}
    reasons.extend(texts[f] for f in v['flags'])
    if complaints:reasons.append(f'{len(complaints)} recent unverified local complaint(s) match this area and service.')
    if unusual['flag']:reasons.append('Isolation Forest marks this price ratio as unusual compared with synthetic normal quotes. Unusual does not mean fraudulent.')
    if not v['flags'] and not complaints:reasons.append('No situation warnings or matching recent local complaints were supplied. Absence of reports is not proof of safety.')
    drivers=models.drivers(ratio,v['flags'],len(complaints),unusual['flag'])
    for driver in drivers[:3]:
        word='raised' if driver['difference']>0 else 'lowered'
        reasons.append(f"Model sensitivity: {driver['signal']} {word} the caution index by {abs(driver['difference'])} points versus replacing that one signal with a neutral value.")
    reasons.append('Sensitivity comparisons are model diagnostics, not causal proof. Other inputs stay unchanged; interacting effects need not add up.')
    score=round((risk['probabilities'].get('Suspicious',0)*.5+risk['probabilities'].get('High Risk',0))*100)
    return {'input':v,'low':low,'high':high,'center':round(center),'mlPrice':round(prediction),'score':score,'verdict':risk['verdict'],'reasons':reasons,'probabilities':risk['probabilities'],'anomaly':unusual,'source':'ML + device traveller median' if enough else 'ML trained on synthetic prices','samples':len(kept),'excluded':len(samples)-len(kept),'confidence':'Limited: synthetic training + unverified local records','night':v['time']=='night' and v['service'] in ['auto','taxi']}

def report_input(r):
    if not isinstance(r,dict):raise ValueError('Expected a report object.')
    v=check_input({**r,'quote':r.get('fare'),'flags':[]})
    if r.get('kind') not in ['fare','complaint','review']:raise ValueError('Invalid report type.')
    note=r.get('note','')
    if not isinstance(note,str) or not 8<=len(note.strip())<=1000:raise ValueError('Note must have 8 to 1,000 characters.')
    try:date=datetime.strptime(r.get('date',''),'%Y-%m-%d')
    except (ValueError,TypeError):raise ValueError('Invalid report date.')
    if not datetime(2020,1,1)<=date<=datetime.now():raise ValueError('Use a past date from 2020 onwards.')
    rating=r.get('rating')
    if isinstance(rating,bool) or not isinstance(rating,int) or not 1<=rating<=5:raise ValueError('Rating must be 1 to 5.')
    return {'id':str(uuid.uuid4()),'city':v['city'],'service':v['service'],'area':v['area'],'time':v['time'],'amount':v['amount'],'fare':v['quote'],'kind':r['kind'],'note':note.strip(),'date':r['date'],'rating':rating,'textResult':models.text_check(note),'hasEvidence':False}

def evidence_ok(body,mime):
    if len(body)>5*1024*1024:raise ValueError('Evidence must be at most 5 MB.')
    ok=(mime=='image/png' and body.startswith(b'\x89PNG\r\n\x1a\n')) or (mime=='image/jpeg' and body.startswith(b'\xff\xd8\xff')) or (mime=='application/pdf' and body.startswith(b'%PDF-')) or (mime=='image/webp' and body.startswith(b'RIFF') and body[8:12]==b'WEBP')
    if not ok:raise ValueError('Evidence must be a valid JPG, PNG, WebP or PDF.')

@app.before_request
def local_only():
    # Prevent foreign websites from posting to a local app (no permissive CORS).
    host=request.host.split(':')[0]
    if host not in ['127.0.0.1','localhost','[::1]']:return jsonify(error='This app is local-only.'),403
    if request.method in ['POST','PUT','DELETE']:
        if request.headers.get('X-Travel-App')!='local':return jsonify(error='Missing local request header.'),403
        origin=request.headers.get('Origin')
        if origin and origin not in ['http://'+request.host,'https://'+request.host]:return jsonify(error='Foreign origin refused.'),403

@app.after_request
def headers(res):
    res.headers['X-Content-Type-Options']='nosniff';res.headers['Referrer-Policy']='no-referrer'
    res.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' blob:; frame-src 'self' blob:; object-src 'none'; base-uri 'self'; form-action 'self'; connect-src 'self'"
    res.headers['Cache-Control']='no-store' if request.path.startswith('/api') else 'no-cache'
    return res
@app.errorhandler(ValueError)
def bad_input(e):return jsonify(error=str(e)),400
@app.errorhandler(413)
def too_big(e):return jsonify(error='Request is too large (30 MB maximum).'),413
@app.errorhandler(500)
def server_error(e):return jsonify(error='Local server failed. Check terminal and available disk space.'),500
@app.get('/')
def home():return send_from_directory(ROOT,'index.html')
@app.get('/<path:name>')
def files(name):
    allowed=['index.html','style.css','app.js','data.js','manifest.webmanifest','sw.js','icons/logo.png','icons/icon-192.png','icons/icon-512.png','icons/maskable-512.png']
    if name not in allowed:return 'Not found',404
    return send_from_directory(ROOT,name)
@app.get('/api/state')
def state():
    reports=rows('reports')
    for r in reports:
        predicted=models.price(r['city'],r['service'],r['amount'],r['time'])
        r['priceAnomaly']=models.unusual(r['fare']/predicted) if r['kind']=='fare' else None
    return jsonify(reports=reports,checks=rows('checks'),metrics=models.metrics)
@app.post('/api/analyze')
def quote():
    result=analyze(request.get_json(silent=True));result['id']=str(uuid.uuid4());result['date']=datetime.now(timezone.utc).isoformat()
    with connect() as db:db.execute('INSERT INTO checks VALUES (?,?)',(result['id'],json.dumps(result)))
    return jsonify(result)
@app.post('/api/reports')
def add_report():
    try:r=json.loads(request.form.get('report','{}'))
    except json.JSONDecodeError:raise ValueError('Invalid report JSON.')
    r=report_input(r);file=request.files.get('evidence');blob=None
    if file and file.filename:
        blob=file.read();evidence_ok(blob,file.mimetype);r['hasEvidence']=True
    with connect() as db:
        db.execute('INSERT INTO reports VALUES (?,?)',(r['id'],json.dumps(r)))
        if blob is not None:db.execute('INSERT INTO evidence VALUES (?,?,?,?)',(r['id'],Path(file.filename).name[:120],file.mimetype,blob))
    return jsonify(r),201
@app.delete('/api/reports/<id>')
def delete_report(id):
    with connect() as db:db.execute('DELETE FROM reports WHERE id=?',(id,));db.execute('DELETE FROM evidence WHERE id=?',(id,))
    return jsonify(ok=True)
@app.delete('/api/checks/<id>')
def delete_check(id):
    with connect() as db:db.execute('DELETE FROM checks WHERE id=?',(id,))
    return jsonify(ok=True)
@app.get('/api/evidence/<id>')
def evidence(id):
    with connect() as db:row=db.execute('SELECT * FROM evidence WHERE id=?',(id,)).fetchone()
    if row is None:return jsonify(error='Evidence not found.'),404
    # Download-only PDF avoids embedding active document content in the application origin.
    return send_file(io.BytesIO(row['body']),mimetype=row['type'],download_name=row['name'],as_attachment=row['type']=='application/pdf')
@app.get('/api/export')
def export():
    with connect() as db:evidence=[{'id':r['id'],'name':r['name'],'type':r['type'],'body':base64.b64encode(r['body']).decode()} for r in db.execute('SELECT * FROM evidence')]
    body={'format':'travel-trap-backup','version':1,'reports':rows('reports'),'evidence':evidence}
    # History is not imported: saved predictions must not be forged by a backup file.
    return jsonify(body)
@app.post('/api/import')
def import_backup():
    body=request.get_json(silent=True)
    if not isinstance(body,dict) or body.get('format')!='travel-trap-backup' or body.get('version')!=1:raise ValueError('Not a compatible backup.')
    reports=body.get('reports');evidence=body.get('evidence')
    if not isinstance(reports,list) or not isinstance(evidence,list) or len(reports)>1000:raise ValueError('Backup has too many or invalid records.')
    valid=[];ids=set();blobs=[]
    for old in reports:
        row=report_input(old);id=old.get('id')
        if not isinstance(id,str) or len(id)>80 or id in ids:raise ValueError('Invalid or repeated report identifier.')
        row['id']=id;ids.add(id);valid.append(row)
    for e in evidence:
        if not isinstance(e,dict) or e.get('id') not in ids or any(x[0]==e.get('id') for x in blobs):raise ValueError('Orphan or repeated evidence.')
        try:blob=base64.b64decode(e.get('body',''),validate=True)
        except Exception:raise ValueError('Invalid evidence encoding.')
        evidence_ok(blob,e.get('type'));name=e.get('name','evidence')
        if not isinstance(name,str):raise ValueError('Invalid evidence name.')
        blobs.append((e['id'],Path(name).name[:120],e['type'],blob))
    for row in valid:row['hasEvidence']=any(b[0]==row['id'] for b in blobs)
    # One transaction, ignore duplicate IDs so repeated backup imports do not inflate sample count.
    with connect() as db:
        added=0
        for row in valid:
            cursor=db.execute('INSERT OR IGNORE INTO reports VALUES (?,?)',(row['id'],json.dumps(row)));added+=cursor.rowcount
            if cursor.rowcount:
                for b in blobs:
                    if b[0]==row['id']:db.execute('INSERT INTO evidence VALUES (?,?,?,?)',b)
    return jsonify(added=added)
@app.delete('/api/data')
def clear_data():
    with connect() as db:
        for table in ['reports','checks','evidence']:db.execute('DELETE FROM '+table)
    return jsonify(ok=True)
if __name__=='__main__':
    print('Travel Trap Detector is local-only. Open http://127.0.0.1:5000 in your browser.')
    from waitress import serve
    serve(app,host='127.0.0.1',port=5000,threads=4)
