const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const trackerPath = fs.existsSync(path.join(__dirname,'../tracker.js')) ? '../tracker.js' : '../public/tracker.js';
const { createTracker } = require(trackerPath);
const base = {event_id:'demo-1',event_name:'request_booking',tour_id:'motlawa',people:2,value:0,currency:'PLN',analytics_consent:true};
const cases = [
 ['valid request is accepted', t=>assert.equal(t.ingest({...base}).accepted,true)],
 ['request is never reported as revenue', t=>{t.ingest({...base});assert.equal(t.events[0]?.value,0)}],
 ['duplicate rejected', t=>{t.ingest({...base});assert.equal(t.ingest({...base}).reason,'duplicate')}],
 ['refusal respected', t=>assert.equal(t.ingest({...base,analytics_consent:false}).reason,'consent_denied')],
 ['denied event is not stored', t=>{t.ingest({...base,analytics_consent:false});assert.equal(t.events.length,0)}],
 ['ID required', t=>assert.equal(t.ingest({...base,event_id:''}).reason,'event_id_missing')],
 ['currency checked', t=>assert.equal(t.ingest({...base,currency:'USD'}).reason,'currency_mismatch')],
 ['purchase cannot masquerade as request', t=>assert.equal(t.ingest({...base,event_name:'purchase'}).reason,'event_name_invalid')],
 ['raw personal data rejected', t=>assert.equal(t.ingest({...base,email:'test@example.invalid'}).reason,'unexpected_fields')],
 ['untrusted tour rejected', t=>assert.equal(t.ingest({...base,tour_id:'unknown'}).reason,'tour_invalid')],
 ['negative people rejected', t=>assert.equal(t.ingest({...base,people:-1}).reason,'people_invalid')],
 ['noninteger people rejected', t=>assert.equal(t.ingest({...base,people:1.5}).reason,'people_invalid')],
 ['commercial value rejected', t=>assert.equal(t.ingest({...base,value:149}).reason,'value_invalid')],
 ['denied ID may be used after consent', t=>{t.ingest({...base,analytics_consent:false});assert.equal(t.ingest({...base}).accepted,true)}],
 ['stored events are defensive copies', t=>{const e={...base};t.ingest(e);e.value=50;assert.equal(t.events[0]?.value,0)}],
];
let failed=0;for(const [name,run] of cases){try{run(createTracker());console.log('PASS '+name)}catch(e){failed++;console.log('FAIL '+name+' — '+e.message)}}
console.log(JSON.stringify({tests:cases.length,failures:failed}));process.exitCode=failed?1:0;
