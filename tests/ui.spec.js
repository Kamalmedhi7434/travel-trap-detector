import {test,expect} from '@playwright/test';
test('demo, reports, evidence, history and responsive screens',async({page,request})=>{
  await request.delete('/api/data',{headers:{'X-Travel-App':'local'}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');await expect(page.locator('#offline-ready')).toContainText('4 ML');
  await page.getByRole('button',{name:'A fair city ride',exact:true}).click();await expect(page.locator('#result .badge')).toHaveText('Fair');
  await page.getByRole('button',{name:'A quote worth questioning',exact:true}).click();await expect(page.locator('#result .badge')).toHaveText('Suspicious');
  await page.getByRole('button',{name:'Pressure + a huge markup',exact:true}).click();await expect(page.locator('#result .badge')).toHaveText('High Risk');
  for(const width of [320,390,1280]){
    await page.setViewportSize({width,height:900});
    for(const route of ['check','explore','reports','history','about']){
      await page.goto('/#'+route);await expect(page.locator('#page-'+route)).toBeVisible();
      expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
      // Show the full result for layout inspection.
      if(route==='check'){await page.getByRole('button',{name:'A fair city ride',exact:true}).click();await expect(page.locator('#result .badge')).toHaveText('Fair');}
      await page.screenshot({path:`screenshots/travel-${route}-${width}.png`,fullPage:true});
    }
  }
  await page.goto('/#reports');const form=page.locator('#report-form');
  await form.locator('[name=fare]').fill('150');await form.locator('[name=note]').fill('<script>alert(1)</script> paid agreed price and got receipt');
  await form.locator('[name=evidence]').setInputFiles('icons/icon-192.png');await form.getByRole('button',{name:'Save to local database'}).click();
  await expect(page.locator('#report-message')).toContainText('Saved');await expect(page.locator('.report-note')).toContainText('<script>');
  await page.getByRole('button',{name:'View evidence'}).click();await expect(page.locator('dialog img')).toBeVisible();await page.getByRole('button',{name:'Close',exact:true}).click();
  await page.reload();await expect(page.locator('.report-note')).toBeVisible();
  await page.goto('/#explore');await expect(page.locator('#area-list')).toContainText('1 local record');
  await page.getByRole('button',{name:'Use my location'}).click();await expect(page.locator('#location-message')).not.toBeEmpty();
  await page.goto('/#history');await expect(page.locator('.history-card').first()).toBeVisible();
  // Block every external URL while still allowing the local backend.
  await page.route('**/*',route=>route.request().url().startsWith('http://127.0.0.1:5000')?route.continue():route.abort());
  await page.goto('/');await page.getByRole('button',{name:'A fair city ride',exact:true}).click();await expect(page.locator('#result .badge')).toHaveText('Fair');
  await page.goto('/#reports');await form.locator('[name=fare]').fill('160');await form.locator('[name=note]').fill('Offline test fare saved with no external access');await form.getByRole('button',{name:'Save to local database'}).click();await expect(page.locator('#report-count')).toContainText('2 LOCAL');
  // Turning off internet is not turning off localhost: the backend must stay accessible.
  // Network requests all stay on localhost; no cloud call is made.
  const urls=[];page.on('request',r=>urls.push(r.url()));await page.goto('/');await page.getByRole('button',{name:'A fair city ride',exact:true}).click();
  expect(urls.every(u=>u.startsWith('http://127.0.0.1:5000'))).toBeTruthy();expect(errors).toEqual([]);
});
