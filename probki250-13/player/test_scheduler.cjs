const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
assert.ok(fs.existsSync(path.join(__dirname,'scheduler.js')),'Scheduling feature missing: implement actual contiguous timeline');
const {shuffleCycle,planNext}=require('./scheduler.js');
let previous=null;
for(let cycle=0;cycle<100;cycle++){
 const order=shuffleCycle(['a','b','c','d','e','f','g'],previous);
 assert.equal(new Set(order).size,7);
 assert.deepEqual([...order].sort(),['a','b','c','d','e','f','g']);
 if(previous)assert.notEqual(order[0],previous);
 previous=order.at(-1);
}
const first=planNext(null,10,4);
assert.ok(first.start>=10.1);
const second=planNext(first.end,10.2,3.5);
assert.equal(second.start,first.end);
assert.equal(second.end,first.end+3.5);
const underrun=planNext(11,12,3);
assert.ok(underrun.underrun);
assert.ok(underrun.start>=12.1);
assert.throws(()=>planNext(null,0,0));
assert.throws(()=>shuffleCycle([],null));
console.log(JSON.stringify({status:'PASS',tested_cycles:100,tracks_per_cycle:7,contiguous_timeline:true,underrun_detected:true}));
