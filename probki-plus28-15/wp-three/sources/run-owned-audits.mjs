import lighthouse from './node_modules/lighthouse/core/index.js';
import desktopConfig from './node_modules/lighthouse/core/config/desktop-config.js';
import {launch} from './node_modules/chrome-launcher/dist/index.js';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));const proof=path.resolve(here,'../..');const out=path.join(proof,'evidence/lighthouse');await fs.mkdir(out,{recursive:true});const summaryPath=path.join(proof,'evidence/lighthouse-summary.json');const prior=process.argv[2]?JSON.parse(await fs.readFile(summaryPath,'utf8')).runs:[];const rows=prior.filter(r=>r.site!==process.argv[2]);
for(const mode of ['mobile','desktop'])for(const [site,port] of [['pf',8797],['property',8798],['retail',8799]]){
 if(process.argv[2]&&site!==process.argv[2])continue;
 const chrome=await launch({chromePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',chromeFlags:['--headless','--disable-gpu','--no-sandbox'],logLevel:'silent'});
 let result;
 try{result=await lighthouse(`http://127.0.0.1:${port}/`,{port:chrome.port,output:['json','html'],onlyCategories:['performance','accessibility','best-practices','seo'],logLevel:'error',throttlingMethod:'simulate',enableErrorReporting:false},mode==='desktop'?desktopConfig:undefined);
 if(result.lhr.runtimeError)throw new Error(JSON.stringify(result.lhr.runtimeError));
 await fs.writeFile(path.join(out,`${site}-${mode}.report.json`),JSON.stringify(result.lhr,null,2));await fs.writeFile(path.join(out,`${site}-${mode}.report.html`),result.report[1]);
 const d=result.lhr;const scores=Object.fromEntries(Object.entries(d.categories).map(([k,v])=>[k,Math.round(v.score*100)]));const metrics=Object.fromEntries(['first-contentful-paint','largest-contentful-paint','speed-index','total-blocking-time','cumulative-layout-shift'].filter(k=>d.audits[k]).map(k=>[k,d.audits[k].numericValue]));
 const row={site,mode,URL:d.finalDisplayedUrl,fetch_time:d.fetchTime,lighthouse_version:d.lighthouseVersion,scores,metrics,report_JSON:`${site}-${mode}.report.json`,report_HTML:`${site}-${mode}.report.html`,environment:d.environment,config:{formFactor:d.configSettings.formFactor,throttlingMethod:d.configSettings.throttlingMethod,throttling:d.configSettings.throttling},local_own_demo_not_client_production:true,hosting_or_field_performance_guarantee:false};rows.push(row);
 const shot=d.audits['final-screenshot']?.details?.data;if(shot?.startsWith('data:image/'))await fs.writeFile(path.join(out,`${site}-${mode}-actual-lh.jpg`),Buffer.from(shot.split(',')[1],'base64'));
 await fs.writeFile(path.join(proof,'evidence/lighthouse-summary.json'),JSON.stringify({status:rows.length===6?'SIX_OFFICIAL_LOCAL_LIGHTHOUSE_RUNS_COMPLETE':'IN_PROGRESS',checked_at:new Date().toISOString(),source_registry:'https://registry.npmjs.org',package:'lighthouse@13.5.0',runner:'Official Lighthouse Node API, same npm engine as CLI; explicit own Chrome cleanup. CLI initially generated report but Windows Node process did not exit, recorded separately.',browser:'Official installed Google Chrome; independent headless runs',not_google_PSI_production_or_field_test:true,runs:rows},null,2));
 console.log(JSON.stringify({site,mode,scores,LCP_ms:metrics['largest-contentful-paint'],CLS:metrics['cumulative-layout-shift']}));
 }finally{await Promise.race([chrome.kill(),new Promise(r=>setTimeout(r,5000))]);}
}
process.exit(0);
