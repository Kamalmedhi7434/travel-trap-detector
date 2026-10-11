import {cities,services,traps,seedFares,demos} from './data.js';
const $=id=>document.getElementById(id);
const money=n=>new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(n);
const safe=value=>String(value).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
let reports=[],checks=[],metrics={},current=null,storageReady=false;
let evidenceUrl=null,installPrompt=null;
async function api(path,options={}){
  const response=await fetch('./api/'+path,{...options,headers:{'X-Travel-App':'local',...(options.headers||{})}});
  const data=await response.json();if(!response.ok)throw Error(data.error||'Local server unavailable.');return data;
}
function jsonPost(data){return {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)};}
function toast(text){$('toast').textContent=text;$('toast').hidden=false;setTimeout(()=>$('toast').hidden=true,4000);}
function cityOptions(select){select.innerHTML+=cities.map(c=>`<option value="${c.id}">${c.name}</option>`).join('');}
function serviceOptions(select){select.innerHTML+=Object.entries(services).map(([id,s])=>`<option value="${id}">${s.name}</option>`).join('');}
function areas(cityId,areaId){const c=cities.find(c=>c.id===$(cityId).value);$(areaId).innerHTML=c.areas.map(a=>`<option>${a}</option>`).join('');}
function unitText(service){const u=services[service].unit;return {km:'Distance (km)',hours:'Duration (hours)',people:'Number of people',nights:'Number of nights'}[u];}
function changeUnit(prefix=''){
  const s=$(prefix+'service').value;$(prefix+'amount-text').textContent=unitText(s);
  const field=prefix?$('report-form').elements.amount:$('amount');field.value=['auto','taxi'].includes(s)?5:1;
}
function page(name,focus=false){
  if(!['check','explore','reports','history','about'].includes(name))name='check';
  document.querySelectorAll('.page').forEach(el=>el.hidden=el.id!=='page-'+name);
  document.querySelectorAll('nav button').forEach(b=>{if(b.dataset.page===name)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
  if(name==='explore')renderExplore();if(name==='reports')renderReports();if(name==='history')renderHistory();
  if(focus){$('main').focus();window.scrollTo(0,0);}
}
function showResult(r){
  current=r;const title=r.verdict==='Fair'?'Looks reasonable.':r.verdict==='Suspicious'?'Pause. Ask a little more.':'Step back before you pay.';
  const advice=r.verdict==='Fair'?'Confirm the all-in total and what is included.':r.verdict==='Suspicious'?'Ask for an itemized price and compare another quote.':'Avoid rushing into payment. Verify the service and seek another quote.';
  $('result').innerHTML=`<div class="section-head"><span class="badge ${r.verdict.replace(' ','')}">${r.verdict}</span><span class="step">02 / UNDERSTAND</span></div><h2>${title}</h2><p class="muted">${safe(cities.find(c=>c.id===r.input.city).name)} · ${safe(services[r.input.service].name)} · ${r.input.amount} ${services[r.input.service].unit}</p><p class="eyebrow">ESTIMATED REASONABLE RANGE</p><div class="price-range">${money(r.low)} - ${money(r.high)}</div><p class="subline muted">You were quoted ${money(r.input.quote)}. Learned-model estimate: ${money(r.mlPrice)}.</p><div class="result-block"><div class="facts-row"><span>Model caution index</span><span>${r.score} / 100</span></div><div class="meter ${r.verdict==='High Risk'?'high':r.verdict==='Suspicious'?'mid':''}"><span style="width:${r.score}%"></span></div><p class="mini muted">Weighted model class probabilities, not probability of a real scam.</p><div class="breakdown">${Object.entries(r.probabilities).map(([k,v])=>`<span>${k}: ${Math.round(v*100)}%</span>`).join('')}</div></div><div class="result-block"><h3>Why this result?</h3><ol class="reasons">${r.reasons.map(reason=>`<li>${safe(reason)}</li>`).join('')}</ol></div><div class="confidence"><strong>${r.source}</strong><br>${r.confidence}. ${r.samples} usable paid-fare record(s), ${r.excluded} excluded outlier(s). Synthetic training is not market validation.</div><div class="result-block"><h3>Your next move</h3><p class="mini">${advice}</p><div class="buttons"><button id="copy-result">Copy summary</button><button id="report-from-check">Add your experience</button></div></div>`;
  $('copy-result').onclick=async()=>{
    const text=`Travel Trap Detector: ${r.verdict}\nQuoted ${money(r.input.quote)}; estimate ${money(r.low)}-${money(r.high)}.\n${r.reasons.join('\n')}\nSynthetic-training ML, not a fraud guarantee.`;
    try{await navigator.clipboard.writeText(text);toast('Summary copied.');}catch{toast('Clipboard unavailable. Use your browser selection to copy.');}
  };
  $('report-from-check').onclick=()=>{
    const f=$('report-form');$('report-city').value=r.input.city;areas('report-city','report-area');$('report-area').value=r.input.area;$('report-service').value=r.input.service;changeUnit('report-');f.elements.amount.value=r.input.amount;f.elements.fare.value=r.input.quote;f.elements.time.value=r.input.time;location.hash='reports';
  };
}
async function runCheck(){
  const button=$('check-form').querySelector('button[type=submit]');button.disabled=true;$('check-error').textContent='';
  try{
    const input={city:$('city').value,area:$('area').value,service:$('service').value,amount:Number($('amount').value),quote:Number($('quote').value),time:$('time').value,flags:[...document.querySelectorAll('[name=flag]:checked')].map(f=>f.value)};
    const result=await api('analyze',jsonPost(input));checks.push(result);showResult(result);if(innerWidth<760)$('result').scrollIntoView({behavior:'smooth',block:'start'});
  }catch(e){$('check-error').textContent=e.message+' Check that app.py is running.';}finally{button.disabled=false;}
}
function renderReports(){
  const list=reports.filter(r=>$('report-filter').value==='all'||r.city===$('report-filter').value).sort((a,b)=>b.date.localeCompare(a.date));
  $('report-count').textContent=reports.length+' LOCAL';
  $('report-list').innerHTML=list.length?list.map(r=>`<article class="report-row"><div class="section-head"><span class="badge">${safe(r.kind)}</span><span class="mini muted">${safe(r.date)}</span></div><h3>${safe(cities.find(c=>c.id===r.city).name)} · ${safe(r.area)}</h3><p>${services[r.service].name} · ${r.amount} ${services[r.service].unit} · ${money(r.fare)} · ${r.rating}/5</p><p class="report-note">${safe(r.note)}</p><p class="mini muted">Text model: ${safe(r.textResult.label)} (${Math.round(r.textResult.confidence*100)}% model confidence). Signals: ${safe(r.textResult.words.join(', ')||'none')}. Unverified.</p><div class="buttons">${r.hasEvidence?`<button data-evidence="${safe(r.id)}">View evidence</button>`:''}<button data-delete="${safe(r.id)}" class="danger-button">Delete</button></div></article>`).join(''):'<div class="empty"><h3>No reports here yet.</h3><p>Add your first experience. Three comparable paid fares can influence your price benchmark.</p></div>';
  document.querySelectorAll('[data-delete]').forEach(b=>b.onclick=async()=>{if(!confirm('Delete this report and its evidence?'))return;try{await api('reports/'+encodeURIComponent(b.dataset.delete),{method:'DELETE'});reports=reports.filter(r=>r.id!==b.dataset.delete);renderReports();}catch(e){toast(e.message);}});
  document.querySelectorAll('[data-evidence]').forEach(b=>b.onclick=()=>openEvidence(b.dataset.evidence));
}
async function openEvidence(id){
  try{
    const res=await fetch('./api/evidence/'+encodeURIComponent(id));if(!res.ok)throw Error('Evidence unavailable.');const blob=await res.blob();
    if(evidenceUrl)URL.revokeObjectURL(evidenceUrl);evidenceUrl=URL.createObjectURL(blob);$('evidence-view').replaceChildren();
    if(blob.type.startsWith('image/')){const img=document.createElement('img');img.src=evidenceUrl;img.alt='Traveller-submitted evidence';$('evidence-view').append(img);}
    else{const link=document.createElement('a');link.href=evidenceUrl;link.download='evidence.pdf';link.textContent='Download saved PDF evidence';$('evidence-view').append(link);}
    $('evidence-dialog').showModal();
  }catch(e){toast(e.message);}
}
function renderHistory(){
  const list=[...checks].sort((a,b)=>b.date.localeCompare(a.date));
  $('history-list').innerHTML=list.map(r=>`<article class="panel history-card"><span class="badge ${r.verdict.replace(' ','')}">${r.verdict}</span><h3>${safe(cities.find(c=>c.id===r.input.city).name)} · ${services[r.input.service].name}</h3><p>${new Date(r.date).toLocaleString()} · ${r.input.amount} ${services[r.input.service].unit}</p><div class="price-range">${money(r.low)} - ${money(r.high)}</div><p>Quoted ${money(r.input.quote)} · ${r.score}/100</p><div class="buttons"><button data-view="${r.id}">View saved result</button><button data-remove="${r.id}" class="danger-button">Delete</button></div></article>`).join('');
  document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{const r=checks.find(c=>c.id===b.dataset.view);showResult(r);location.hash='check';setTimeout(()=>$('result').scrollIntoView(),50);});
  document.querySelectorAll('[data-remove]').forEach(b=>b.onclick=async()=>{try{await api('checks/'+b.dataset.remove,{method:'DELETE'});checks=checks.filter(c=>c.id!==b.dataset.remove);renderHistory();}catch(e){toast(e.message);}});
}
function renderExplore(){
  const c=cities.find(c=>c.id===$('explore-city').value), service=$('explore-service').value;
  const local=reports.filter(r=>r.city===c.id&&(service==='all'||r.service===service));
  const visible=traps.filter(t=>service==='all'||t.services.includes(service));
  const positions=[[82,66],[238,83],[103,169],[257,185]];
  $('area-map').innerHTML=`<svg class="area-svg" viewBox="0 0 340 250" role="img" aria-label="Illustrative area diagram of ${c.name}. Not a street map."><path d="M0 105 Q 125 200 340 116" stroke="#dbece4" stroke-width="35" fill="none"/><path d="M0 48L340 230M125 0L182 250M0 225L340 40" stroke="#d8dedb" stroke-width="8"/>${c.areas.map((a,i)=>`<circle cx="${positions[i][0]}" cy="${positions[i][1]}" r="17" fill="${local.some(r=>r.area===a&&r.kind==='complaint')?'#b72431':'#25695a'}"/><text x="${positions[i][0]}" y="${positions[i][1]+5}" text-anchor="middle" fill="white" font-size="13">${i+1}</text>`).join('')}<text x="12" y="240" font-size="10" fill="#585254">Illustrative layout · not to scale</text></svg>`;
  $('area-list').innerHTML=c.areas.map((a,i)=>{
    const rows=local.filter(r=>r.area===a),bad=rows.filter(r=>r.kind==='complaint');const fares=rows.filter(r=>r.kind==='fare');const unusual=fares.filter(r=>r.priceAnomaly?.flag);
    return `<div class="area-row"><h3>${i+1}. ${safe(a)}</h3><p>${rows.length} local record(s) · ${bad.length} unverified complaint(s) · ${fares.length} paid fares · ${unusual.length} ML price outlier(s)</p><p class="mini muted">${rows.length?'Review records before drawing conclusions.':'No local data yet. No safety conclusion available.'}</p><button data-area="${i}">Check a quote here</button></div>`;
  }).join('');
  $('service-list').innerHTML=Object.entries(services).map(([id,s])=>{
    const examples=seedFares.filter(f=>f.city===c.id&&f.service===id);return `<div class="area-row"><h3>${s.name}</h3><p>${money(Math.min(...examples.map(f=>f.fare)))} - ${money(Math.max(...examples.map(f=>f.fare)))} / ${id==='auto'||id==='taxi'?'5 km':'1 '+s.unit}</p><p class="mini muted">3 illustrative history samples. Not real traveller reports.</p><button data-service="${id}">Analyze ${s.name.toLowerCase()}</button></div>`;
  }).join('');
  $('traps').innerHTML=visible.map(t=>`<article class="panel trap-card"><p class="trap-type">${t.type} · example pattern</p><h2>${t.name}</h2><p>${t.text}</p><p class="mini muted">Illustrative context: ${safe(c.areas[t.area])}. Not a real incident or area accusation.</p><p class="trap-action">${t.action}</p></article>`).join('');
  document.querySelectorAll('[data-area]').forEach(b=>b.onclick=()=>{$('city').value=c.id;areas('city','area');$('area').selectedIndex=Number(b.dataset.area);location.hash='check';});
  document.querySelectorAll('[data-service]').forEach(b=>b.onclick=()=>{$('city').value=c.id;areas('city','area');$('service').value=b.dataset.service;changeUnit();location.hash='check';});
}
function distance(a,b){const rad=n=>n*Math.PI/180;const t=Math.sin(rad(b.lat-a.lat)/2)**2+Math.cos(rad(a.lat))*Math.cos(rad(b.lat))*Math.sin(rad(b.lon-a.lon)/2)**2;return 6371*2*Math.atan2(Math.sqrt(t),Math.sqrt(1-t));}
function offlineStatus(){$('online').textContent=navigator.onLine?'● Local app':'● Internet offline';}
async function loadState(){const s=await api('state');reports=s.reports;checks=s.checks;metrics=s.metrics;storageReady=true;}
async function init(){
  ['city','report-city','explore-city','report-filter'].forEach(id=>cityOptions($(id)));
  ['service','report-service','explore-service'].forEach(id=>serviceOptions($(id)));
  areas('city','area');areas('report-city','report-area');
  $('city').onchange=()=>areas('city','area');$('report-city').onchange=()=>areas('report-city','report-area');
  $('service').onchange=()=>changeUnit();$('report-service').onchange=()=>changeUnit('report-');
  const today=new Date();const date=new Date(today.getTime()-today.getTimezoneOffset()*60000).toISOString().slice(0,10);
  $('report-form').elements.date.value=date;$('report-form').elements.date.max=date;
  $('demos').innerHTML=demos.map((d,i)=>`<button data-demo="${i}">${d.name}</button>`).join('');
  document.querySelectorAll('[data-demo]').forEach(b=>b.onclick=()=>{const d=demos[Number(b.dataset.demo)];$('city').value=d.city;areas('city','area');$('area').value=d.area;$('service').value=d.service;changeUnit();$('amount').value=d.amount;$('quote').value=d.quote;$('time').value='day';document.querySelectorAll('[name=flag]').forEach(f=>f.checked=d.flags.includes(f.value));runCheck();});
  document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{location.hash=b.dataset.page;page(b.dataset.page,true);});
  window.addEventListener('hashchange',()=>page(location.hash.slice(1)));
  $('check-form').onsubmit=e=>{e.preventDefault();runCheck();};
  $('explore-city').onchange=renderExplore;$('explore-service').onchange=renderExplore;$('report-filter').onchange=renderReports;
  $('locate').onclick=()=>{
    if(!navigator.geolocation){$('location-message').textContent='Location is not supported. Choose a city manually.';return;}
    $('location-message').textContent='Waiting for your location permission…';
    navigator.geolocation.getCurrentPosition(pos=>{
      const point={lat:pos.coords.latitude,lon:pos.coords.longitude};const sorted=cities.map(c=>({...c,km:distance(point,c)})).sort((a,b)=>a.km-b.km);
      if(sorted[0].km>80){$('location-message').textContent='You are outside supported city areas. Choose a city manually.';return;}
      $('explore-city').value=sorted[0].id;$('location-message').textContent=`Nearest supported city: ${sorted[0].name}, about ${Math.round(sorted[0].km)} km from its centre. GPS accuracy ±${Math.round(pos.coords.accuracy)} m. No precise nearby provider search.`;renderExplore();
    },()=>{$('location-message').textContent='Location unavailable or denied. Choose a city manually.';},{timeout:10000,maximumAge:0});
  };
  $('report-form').onsubmit=async e=>{
    e.preventDefault();const f=e.target,button=f.querySelector('[type=submit]');button.disabled=true;
    try{const r=Object.fromEntries(new FormData(f));r.amount=Number(r.amount);r.fare=Number(r.fare);r.rating=Number(r.rating);delete r.evidence;
      const data=new FormData();data.append('report',JSON.stringify(r));if(f.elements.evidence.files[0])data.append('evidence',f.elements.evidence.files[0]);
      const saved=await api('reports',{method:'POST',body:data});reports.push(saved);await loadState();renderReports();f.elements.note.value='';f.elements.evidence.value='';$('report-message').textContent='Saved to local SQLite. Text model: '+saved.textResult.label+'.';
    }catch(err){$('report-message').textContent=err.message;}finally{button.disabled=false;}
  };
  $('close-evidence').onclick=()=>$('evidence-dialog').close();$('evidence-dialog').addEventListener('close',()=>{if(evidenceUrl)URL.revokeObjectURL(evidenceUrl);evidenceUrl=null;$('evidence-view').replaceChildren();});
  $('export').onclick=async()=>{try{const data=await api('export');const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='travel-trap-backup.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),3000);$('data-message').textContent='Backup downloaded. Contains reports and evidence, not prediction history. Keep it private.';}catch(e){$('data-message').textContent=e.message;}};
  $('import').onchange=async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>30*1024*1024)throw Error('Backup exceeds 30 MB.');const data=JSON.parse(await file.text());const result=await api('import',jsonPost(data));await loadState();renderReports();$('data-message').textContent=`Imported ${result.added} new report(s). Duplicate IDs were skipped.`;}catch(err){$('data-message').textContent='Import failed: '+err.message;}finally{e.target.value='';}};
  $('clear').onclick=async()=>{if(!confirm('Permanently erase all local reports, history and evidence? Export first if needed.'))return;try{await api('data',{method:'DELETE'});reports=[];checks=[];renderReports();renderHistory();current=null;$('result').innerHTML='<div class="empty"><h2>Local data erased.</h2><p>Run a new check to start again.</p></div>';$('data-message').textContent='All local data erased.';}catch(e){$('data-message').textContent=e.message;}};
  window.addEventListener('online',offlineStatus);window.addEventListener('offline',offlineStatus);offlineStatus();
  window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();installPrompt=e;$('install').hidden=false;});$('install').onclick=async()=>{if(installPrompt){await installPrompt.prompt();installPrompt=null;$('install').hidden=true;}};
  try{await loadState();$('offline-ready').textContent='Local backend ready · all 4 ML models loaded';}
  catch(e){$('offline-ready').textContent='Backend unavailable. Run python app.py.';$('check-error').textContent=e.message;}
  if('serviceWorker' in navigator){try{await navigator.serviceWorker.register('./sw.js');}catch(e){console.warn('App shell cache unavailable',e);}}
  page(location.hash.slice(1));
}
init();
