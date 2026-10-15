import test from 'node:test';
import assert from 'node:assert/strict';
let calculate=null;
try { ({ calculate } = await import('./calculator.mjs')); } catch (e) { if(e.code !== 'ERR_MODULE_NOT_FOUND') throw e; }
const catalog={moba:{label:'MOBA — dane demo',levels:['bronze','silver','gold','platinum','diamond'],step_minor:[2500,3000,4500,6000],servers:{eu:{extra_minor:0},na:{extra_minor:1000}}},fps:{label:'FPS — dane demo',levels:['bronze','silver','gold','platinum'],step_minor:[4000,5500,7000],servers:{eu:{extra_minor:0},na:{extra_minor:1500}}}};
const request=(fields={})=>({game:'moba',server:'eu',from:'bronze',to:'platinum',priority:false,streaming:false,...fields});
const run=(fields)=>{assert.equal(typeof calculate,'function','Price engine must be implemented');return calculate(catalog,request(fields));};
test('sums the crossed segments, not a flat rank count',()=>{assert.equal(run().base_minor,10000);assert.equal(run().total_minor,10000);});
test('a single step is exactly 2500 minor units',()=>assert.equal(run({to:'silver'}).total_minor,2500));
test('higher starting rank omits earlier segments',()=>assert.equal(run({from:'silver'}).base_minor,7500));
test('FPS uses its own price path',()=>assert.equal(run({game:'fps'}).total_minor,16500));
test('priority adds 15 percent once',()=>assert.equal(run({priority:true}).total_minor,11500));
test('two options add 25 percent, not compounded 26.5 percent',()=>assert.equal(run({priority:true,streaming:true}).total_minor,12500));
test('rounds currency in minor units once, half-up',()=>{assert.equal(typeof calculate,'function');const own={test:{levels:['a','b'],step_minor:[2999],servers:{eu:{extra_minor:0}}}};assert.equal(calculate(own,{game:'test',server:'eu',from:'a',to:'b',priority:true,streaming:false}).total_minor,3449);});
for(const [name,fields] of [['same target',{to:'bronze'}],['lower target',{from:'gold',to:'silver'}],['unknown game',{game:'unknown'}],['unknown start',{from:'missing'}],['unknown target',{to:'missing'}],['prototype game',{game:'__proto__'}],['nonboolean option',{priority:'yes'}]])test('rejects '+name,()=>{assert.equal(typeof calculate,'function');assert.throws(()=>calculate(catalog,request(fields)));});
test('rejects a malformed price table instead of returning a wrong amount',()=>{assert.equal(typeof calculate,'function');assert.throws(()=>calculate({moba:{levels:['bronze','silver'],step_minor:[-1]}},request({to:'silver'})));});
test('does not mutate catalogue or request',()=>{assert.equal(typeof calculate,'function');const before=JSON.stringify(catalog),r=request(),rBefore=JSON.stringify(r);calculate(catalog,r);assert.equal(JSON.stringify(catalog),before);assert.equal(JSON.stringify(r),rBefore);});
test('adds the selected server price once',()=>assert.equal(run({server:'na'}).total_minor,11000));
test('rejects unknown server instead of silently using the default',()=>{assert.equal(typeof calculate,'function');assert.throws(()=>calculate(catalog,request({server:'missing'})));});
