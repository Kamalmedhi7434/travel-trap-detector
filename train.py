"""Train four small offline models. All training records are synthetic demo data."""
from pathlib import Path
import csv, json
import numpy as np
import joblib
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score

ROOT = Path(__file__).resolve().parent
CITIES = {'guwahati':1, 'jaipur':1.05, 'delhi':1.2, 'agra':1, 'varanasi':.95, 'goa':1.4, 'shillong':1.15, 'kolkata':1.1}
SERVICES = {'auto':(35,18,60), 'taxi':(70,25,120), 'guide':(0,400,400), 'meal':(0,220,220), 'activity':(0,450,450), 'hotel':(0,1600,1600)}
RISK_FEATURES = ['quote_ratio','unclear_extras','payment_pressure','diversion','no_receipt','complaints','price_anomaly']
TEXT_EXAMPLES = {
 'hidden charges': ['extra charge added after the ride','bill had hidden parking fees','price changed at the end','unexpected tax not in the quote','charged extra for luggage','room total had undisclosed fees','menu price different from final bill','asked to pay waiting charges not agreed','undisclosed service fee was added','entry fee excluded from quoted price'],
 'payment pressure': ['demanded cash immediately before details','pressured me to pay advance now','would not let me compare prices','urgent deposit required without receipt','insisted on instant payment','said pay now or lose booking','rushed me to hand over money','demanded advance before seeing the room','refused time to check the total','pushy payment request before confirmation'],
 'diversion': ['driver took us to an unrequested shop','said destination closed and sold another tour','guide redirected us to a commission store','changed route without asking','took a long detour to a shop','insisted on another hotel instead','unwanted shopping stop during trip','refused the agreed destination','driver suggested a closed monument and new tour','drove to another market without permission'],
 'positive': ['paid agreed price and got receipt','helpful guide clear total good experience','fair price no extra fees','clean room with all charges explained','driver followed route and price','meal matched menu total','good service transparent pricing','everything as promised and no pressure','polite driver and correct destination','reasonable price and honest service']
}

def train():
    rng = np.random.default_rng(42)
    models = ROOT / 'models'; models.mkdir(exist_ok=True)
    data_dir = ROOT / 'data'; data_dir.mkdir(exist_ok=True)
    rows, target, records = [], [], []
    # Each city/service pair has a separate learned line: intercept + quantity + night.
    for city, factor in CITIES.items():
        for service, (base, rate, minimum) in SERVICES.items():
            for _ in range(140):
                amount = float(rng.uniform(1,40) if service in ['auto','taxi'] else rng.uniform(1,8))
                night = int(rng.integers(0,2)) if service in ['auto','taxi'] else 0
                fair = max(minimum,base + rate*amount)*factor*(1+.2*night)
                paid = round(fair * rng.uniform(.82,1.18),2)
                rows.append([city+'_'+service,amount,amount*night,night]); target.append(paid)
                records.append([city,service,round(amount,3),night,paid,'synthetic'])
    rows=np.array(rows,dtype=object); target=np.array(target)
    # Interactions let every city/service learn its own slope, rather than one shared slope.
    # The final vector is built by fare_features() below and fitted with ordinary ridge regression.
    X=np.array([fare_features(row[0].split('_')[0],row[0].split('_')[1],float(row[1]),bool(row[3])) for row in rows])
    X_train,X_test,y_train,y_test=train_test_split(X,target,test_size=.2,random_state=42)
    fare=Ridge(alpha=.1,fit_intercept=False).fit(X_train,y_train)
    pred=fare.predict(X_test)
    residual=float(np.quantile(np.abs(y_test-pred)/np.maximum(pred,1),.9))
    joblib.dump(fare,models/'fare.joblib')
    # Train a classifier on simulated situations. Labels describe demo policy, not verified fraud.
    Xrisk=[]; yrisk=[]
    for _ in range(6500):
        ratio=float(rng.uniform(.4,3.5)); flags=rng.integers(0,2,4).tolist(); count=int(rng.integers(0,6))
        anomaly=int(ratio<.65 or ratio>1.55)
        points=(65 if ratio>2.5 else 45 if ratio>1.875 else 25 if ratio>1.4375 else 12 if ratio>1.25 else 0)+min(30,flags[0]*10+sum(flags[1:])*15)+min(15,count*5)
        label='High Risk' if points>=60 else 'Suspicious' if points>=25 else 'Fair'
        Xrisk.append([ratio,*flags,count,anomaly]);yrisk.append(label)
    a,b,c,d=train_test_split(Xrisk,yrisk,test_size=.2,random_state=42,stratify=yrisk)
    risk=RandomForestClassifier(n_estimators=90,max_depth=9,min_samples_leaf=4,random_state=42,n_jobs=1).fit(a,c)
    risk_pred=risk.predict(b)
    joblib.dump(risk,models/'risk.joblib')
    normal=np.column_stack([rng.uniform(.82,1.18,1500),rng.uniform(.82,1.18,1500)])
    anomaly=IsolationForest(n_estimators=100,contamination=.03,random_state=42).fit(normal)
    joblib.dump(anomaly,models/'anomaly.joblib')
    texts=[];labels=[]
    for label,examples in TEXT_EXAMPLES.items():
        for sentence in examples:
            texts.append(sentence); labels.append(label)
    ta,tb,la,lb=train_test_split(texts,labels,test_size=.2,random_state=42,stratify=labels)
    text=make_pipeline(TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True),LogisticRegression(C=5,max_iter=1000,random_state=42)).fit(ta,la)
    text_accuracy=accuracy_score(lb,text.predict(tb))
    # Refit on all examples for the delivered model, keep holdout metric honest.
    text.fit(texts,labels); joblib.dump(text,models/'text.joblib')
    metrics={'data':'SYNTHETIC DEMO ONLY','seed':42,'fare_rows':len(rows),'fare_test_rows':len(y_test),'fare_mae_rupees':round(mean_absolute_error(y_test,pred),2),'fare_relative_error_90pct':round(residual,4),'risk_rows':len(Xrisk),'risk_accuracy':round(accuracy_score(d,risk_pred),4),'risk_feature_names':RISK_FEATURES,'risk_feature_importance':[round(float(v),4) for v in risk.feature_importances_],'text_examples':len(texts),'text_holdout_accuracy':round(text_accuracy,4),'anomaly_training_rows':1500,'warning':'Synthetic holdout metrics do not measure accuracy on real travellers, real fares or actual scams.'}
    (models/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    with (data_dir/'fare_training.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(['city','service','amount','night','paid','source']);writer.writerows(records)
    with (data_dir/'risk_training.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(RISK_FEATURES+['label','source']);writer.writerows([row+[label,'synthetic'] for row,label in zip(Xrisk,yrisk)])
    with (data_dir/'anomaly_training.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(['ratio_a','ratio_b']);writer.writerows(normal)
    (data_dir/'text_training.json').write_text(json.dumps(TEXT_EXAMPLES,indent=2),encoding='utf-8')
    print(json.dumps(metrics,indent=2)); print('Saved fare, risk, anomaly and text models in models/. Restart app.py after retraining.')

def fare_features(city,service,amount,night):
    values=[]
    for c in CITIES:
        for s in SERVICES:
            same=int(city==c and service==s)
            values.extend([same,same*amount,same*amount*int(night),same*int(night)])
    return values

if __name__=='__main__': train()
