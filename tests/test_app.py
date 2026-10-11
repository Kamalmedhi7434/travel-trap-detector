import os, tempfile, unittest, json, io
from datetime import date
# Never run tests against the owner's real database.
os.environ['TRAVEL_DB']=tempfile.mktemp(suffix='.db')
from app import app, analyze, models, DB
class AppTests(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client();self.header={'X-Travel-App':'local'}
        self.client.delete('/api/data',headers=self.header)
    def quote(self,**values):
        data={'city':'guwahati','service':'auto','amount':5,'quote':140,'area':'City centre','time':'day','flags':[]};data.update(values)
        return self.client.post('/api/analyze',json=data,headers=self.header)
    def report(self,**values):
        r={'city':'guwahati','service':'auto','amount':5,'fare':140,'area':'City centre','time':'day','kind':'fare','note':'Paid agreed price and got receipt','date':date.today().isoformat(),'rating':5};r.update(values)
        return self.client.post('/api/reports',data={'report':json.dumps(r)},headers=self.header)
    def test_models_loaded(self):
        self.assertEqual(models.metrics['fare_rows'],6720)
        self.assertGreater(models.price('guwahati','auto',10,'day'),models.price('guwahati','auto',5,'day'))
    def test_verdicts(self):
        self.assertEqual(self.quote().json['verdict'],'Fair')
        self.assertEqual(self.quote(city='jaipur',service='taxi',amount=8,quote=420,area='Station area',flags=['extras']).json['verdict'],'Suspicious')
        self.assertEqual(self.quote(city='goa',service='guide',amount=2,quote=3500,area='Beach approach',flags=['pressure','diversion']).json['verdict'],'High Risk')
    def test_validation(self):
        for v in [0,-1,'bad',float('inf')]:self.assertEqual(self.quote(amount=v).status_code,400)
        self.assertEqual(self.quote(city='unknown').status_code,400)
        self.assertEqual(self.report(note='bad').status_code,400)
    def test_report_changes_benchmark(self):
        for fare in [180,185,190]:self.assertEqual(self.report(fare=fare).status_code,201)
        result=self.quote().json;self.assertEqual(result['samples'],3);self.assertIn('median',result['source'])
    def test_complaint_not_benchmark(self):
        self.report(kind='complaint',fare=900)
        result=self.quote().json;self.assertEqual(result['samples'],0);self.assertTrue(any('complaint' in s for s in result['reasons']))
    def test_anomaly(self):
        self.assertTrue(models.unusual(4)['flag']);self.assertFalse(models.unusual(1)['flag'])
    def test_text_unknown(self):
        self.assertEqual(models.text_check('xyzqv abcxyz')['label'],'unclear')
        self.assertEqual(models.text_check('extra charge added after the ride')['label'],'hidden charges')
    def test_backup_idempotence(self):
        self.report();backup=self.client.get('/api/export').json
        self.assertEqual(self.client.post('/api/import',json=backup,headers=self.header).json['added'],0)
        self.client.delete('/api/data',headers=self.header)
        self.assertEqual(self.client.post('/api/import',json=backup,headers=self.header).json['added'],1)
    def test_backup_invalid_atomic(self):
        self.report();backup=self.client.get('/api/export').json;backup['reports'].append({'bad':1})
        self.assertEqual(self.client.post('/api/import',json=backup,headers=self.header).status_code,400)
        self.assertEqual(len(self.client.get('/api/state').json['reports']),1)
    def test_security(self):
        self.assertEqual(self.client.post('/api/analyze',json={}).status_code,403)
        self.assertEqual(self.client.delete('/api/data',headers={**self.header,'Origin':'https://evil.invalid'}).status_code,403)
        self.assertEqual(self.client.get('/data/travel.db').status_code,404)
        self.assertEqual(self.client.get('/models/fare.joblib').status_code,404)
    def test_evidence_rejected(self):
        r={'city':'guwahati','service':'auto','amount':5,'fare':140,'area':'City centre','time':'day','kind':'fare','note':'Receipt attached for this ride','date':date.today().isoformat(),'rating':4}
        res=self.client.post('/api/reports',data={'report':json.dumps(r),'evidence':(io.BytesIO(b'<script>bad</script>'),'photo.png','image/png')},headers=self.header)
        self.assertEqual(res.status_code,400);self.assertEqual(len(self.client.get('/api/state').json['reports']),0)
    def test_deletion(self):
        r=self.report().json;self.client.delete('/api/reports/'+r['id'],headers=self.header)
        self.assertEqual(self.client.get('/api/state').json['reports'],[])
if __name__=='__main__':unittest.main()
