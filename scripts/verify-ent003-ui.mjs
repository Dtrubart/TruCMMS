import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import path from 'node:path';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.TRUCMMS_PLAYWRIGHT_MODULE || 'playwright');
const password=process.env.TRUCMMS_UI_PASSWORD;assert.ok(password,'Set TRUCMMS_UI_PASSWORD privately.');
assert.ok(process.env.TRUCMMS_ORG_FIXTURE_FILE,'Set the private TRUCMMS_ORG_FIXTURE_FILE path.');
const fixture=JSON.parse(fs.readFileSync(process.env.TRUCMMS_ORG_FIXTURE_FILE,'utf8'));
const base=(process.env.TRUCMMS_BASE_URL||'http://test.vanbags.localhost:8100').replace(/\/$/,'');
const expectedSite=new URL(base).hostname;
const artifacts=path.resolve(process.env.TRUCMMS_UI_ARTIFACT_DIR||'test-results/ent003');fs.mkdirSync(artifacts,{recursive:true});
const browser=await chromium.launch({channel:process.env.TRUCMMS_BROWSER_CHANNEL||(process.platform==='win32'?'msedge':undefined),headless:true,args:['--host-resolver-rules=MAP *.vanbags.localhost 127.0.0.1']});
const errors=[],checks=[];
async function login(context,user,password){
 const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));await page.goto(base+'/login');
 await page.locator('#login_email').fill(user);await page.locator('#login_password').fill(password);
 await page.locator('.btn-login:not(.btn-login-with-email-link)').click();await page.waitForURL(url=>!url.pathname.includes('login'));
 await page.goto(base+'/desk');await page.waitForFunction(site=>window.frappe?.boot?.sitename===site&&frappe.csrf_token,expectedSite);
 return page;
}
async function openOrganization(page){
 await page.evaluate(values=>{frappe.route_options={company:values.company,unit:values.units[0]};frappe.set_route('trucmms-organization');},fixture);
 await page.locator('.trucmms-organization h3').waitFor();
 const root=page.locator('.trucmms-organization .tree .tree-label').filter({hasText:'ENT003 UI Region'}).first();
 await root.waitFor();assert.equal(await root.getAttribute('data-name'),fixture.units[0]);await root.click();
 await page.locator('.trucmms-organization .tree .tree-label').filter({hasText:'ENT003 UI District A'}).waitFor();
}
const adminContext=await browser.newContext(),readerContext=await browser.newContext();
try{
 const page=await login(adminContext,process.env.TRUCMMS_UI_USER||'Administrator',password);await openOrganization(page);
 await page.locator('.trucmms-organization .tree .tree-label').filter({hasText:'ENT003 UI Hidden District B'}).waitFor();
 await page.locator('.trucmms-organization .tree .tree-label').filter({hasText:'ENT003 UI District A'}).click();
 await page.getByRole('button',{name:'ENT003 UI Site A',exact:true}).waitFor();
 checks.push('admin tree renders actual root and both districts; current site membership visible');
 await page.getByRole('button',{name:'ENT003 UI Site A',exact:true}).click();
 await page.waitForFunction(site=>window.cur_frm?.doctype==='TruCMMS Site'&&cur_frm.doc.name===site,fixture.sites[0]);
 await page.getByRole('button',{name:'Asignar unidad operativa',exact:true}).click();
 await page.waitForFunction(()=>window.cur_dialog?.get_field('unit'));
 await page.evaluate(async values=>{await cur_dialog.set_value('unit',values.units[0]);await cur_dialog.set_value('reason','Synthetic UI membership change');},fixture);
 await page.locator('.modal:visible').last().getByRole('button',{name:'Ver impacto',exact:true}).click();
 const yesLabel=await page.evaluate(()=>__('Yes'));
 await page.getByRole('dialog').getByRole('button',{name:yesLabel,exact:true}).click();
 await page.waitForFunction(unit=>cur_frm.doc.operating_unit===unit,fixture.units[0]);
 checks.push('native Site form previews and confirms administrative membership');
 await page.evaluate(async values=>{const{message:preview}=await frappe.call({method:'vanbags_maintenance.operating_units.preview_site',args:{site:values.sites[0],unit:values.units[1]}});await frappe.call({method:'vanbags_maintenance.operating_units.assign_site',args:{site:values.sites[0],unit:values.units[1],token:preview.token,reason:'Restore synthetic UI membership'}});},fixture);
 const reader=await login(readerContext,fixture.reader,fixture.password);await openOrganization(reader);
 assert.equal(await reader.locator('.trucmms-organization .tree .tree-label').filter({hasText:'ENT003 UI Hidden District B'}).count(),0);
 await reader.locator('.trucmms-organization .tree .tree-label').filter({hasText:'ENT003 UI District A'}).click();
 await reader.getByRole('button',{name:'ENT003 UI Site A',exact:true}).waitFor();
 assert.equal(await reader.getByRole('button',{name:'ENT003 UI Site B',exact:true}).count(),0);
 assert.equal(await reader.getByRole('button',{name:'Cambiar estructura operativa',exact:true}).count(),0);
 const forbidden=await reader.request.get(base+'/api/method/vanbags_maintenance.operating_units.details',{params:{name:fixture.units[2]}});
 assert.equal(forbidden.status(),403);
 const title=await reader.request.get(base+'/api/method/frappe.desk.search.get_link_title',{params:{doctype:'TruCMMS Operating Unit',docname:fixture.units[2]}});
 assert.equal(title.status(),403);
 checks.push('scoped reader sees only authorized branch/site; direct foreign-unit and native link-title APIs denied');
 await reader.screenshot({path:path.join(artifacts,'ent003-organization-reader-desktop.png'),fullPage:true});
 await reader.setViewportSize({width:390,height:844});await reader.mouse.click(375,350);await reader.waitForTimeout(350);
 await reader.screenshot({path:path.join(artifacts,'ent003-organization-reader-mobile.png'),fullPage:true});
 assert.ok(await reader.locator('.trucmms-organization').evaluate(el=>el.scrollWidth-el.clientWidth)<=2);
 checks.push('390px organization layout without horizontal overflow');
 assert.deepEqual(errors,[]);
 const result={ok:true,checks,jsErrors:errors,synthetic_membership_changes:2};
 fs.writeFileSync(path.join(artifacts,'ent003-ui-results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}finally{await readerContext.close();await adminContext.close();await browser.close();}
