(function(root){
 'use strict';
 function shuffleCycle(items,last){
   if(!Array.isArray(items)||!items.length)throw new Error('Empty catalog');
   const order=[...items];
   for(let i=order.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[order[i],order[j]]=[order[j],order[i]];}
   if(order.length>1&&order[0]===last)[order[0],order[1]]=[order[1],order[0]];
   return order;
 }
 function planNext(queuedEnd,now,duration){
   if(!Number.isFinite(now)||!Number.isFinite(duration)||duration<=0)throw new Error('Invalid scheduling input');
   const underrun=queuedEnd!==null&&queuedEnd<now;
   const start=queuedEnd===null||underrun?now+.15:queuedEnd;
   return {start,end:start+duration,underrun};
 }
 const api={shuffleCycle,planNext};
 if(typeof module==='object'&&module.exports)module.exports=api;
 root.PlayerScheduling=api;
})(typeof globalThis==='object'?globalThis:this);
