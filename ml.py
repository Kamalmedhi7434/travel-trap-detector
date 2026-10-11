"""Small, readable wrapper around the four trained models."""
from pathlib import Path
import json
import joblib
import numpy as np
from train import fare_features
ROOT=Path(__file__).resolve().parent
class Models:
    def __init__(self):
        self.fare=joblib.load(ROOT/'models/fare.joblib')
        self.risk=joblib.load(ROOT/'models/risk.joblib')
        self.anomaly=joblib.load(ROOT/'models/anomaly.joblib')
        self.text=joblib.load(ROOT/'models/text.joblib')
        self.metrics=json.loads((ROOT/'models/metrics.json').read_text())
    def price(self,city,service,amount,time):
        night=time=='night' and service in ['auto','taxi']
        return max(1,float(self.fare.predict([fare_features(city,service,amount,night)])[0]))
    def unusual(self,ratio):
        value=float(self.anomaly.decision_function([[ratio,ratio]])[0])
        return {'flag':value<0,'score':round(value,4),'explanation':'Negative isolation score means the quote lies outside the learned synthetic normal-price cluster.'}
    def text_check(self,note):
        vector=self.text[0].transform([note]);probs=self.text.predict_proba([note])[0]
        best=int(np.argmax(probs));confidence=float(probs[best]);label=str(self.text.classes_[best])
        words=[]
        if vector.nnz:
            names=self.text[0].get_feature_names_out();coefs=self.text[1].coef_[best]
            for idx in sorted(vector.indices,key=lambda i:coefs[i]*vector[0,i],reverse=True)[:5]:
                if coefs[idx]*vector[0,idx]>0:words.append(str(names[idx]))
        if not vector.nnz or confidence<.45:label='unclear'
        return {'label':label,'confidence':round(confidence,3),'words':words,'note':'English demo text model. Predicted category is not proof of a complaint.'}
    def classify(self,ratio,flags,complaints,anomaly):
        values=[ratio,*[int(key in flags) for key in ['extras','pressure','diversion','receipt']],min(5,complaints),int(anomaly)]
        probabilities=self.risk.predict_proba([values])[0];best=int(np.argmax(probabilities))
        return {'verdict':str(self.risk.classes_[best]),'probabilities':{str(c):round(float(p),3) for c,p in zip(self.risk.classes_,probabilities)},'confidence':round(float(probabilities[best]),3)}

    def drivers(self,ratio,flags,complaints,anomaly):
        # Compare the prediction with each signal replaced by a neutral value.
        values=[ratio,*[int(key in flags) for key in ['extras','pressure','diversion','receipt']],min(5,complaints),int(anomaly)]
        names=['price ratio','unclear extras','payment pressure','diversion','no receipt','local complaints','price anomaly']
        neutral=[1,0,0,0,0,0,0]
        def caution(x):
            p=self.risk.predict_proba([x])[0]
            return sum(float(value)*(1 if cls=='High Risk' else .5 if cls=='Suspicious' else 0) for cls,value in zip(self.risk.classes_,p))*100
        base=caution(values);out=[]
        for i in range(len(values)):
            if values[i]==neutral[i]:continue
            changed=values.copy();changed[i]=neutral[i]
            delta=round(base-caution(changed),1)
            if abs(delta)>=1:out.append({'signal':names[i],'difference':delta})
        return sorted(out,key=lambda row:abs(row['difference']),reverse=True)
