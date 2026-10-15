import { calculate } from './calculator.mjs';
import { catalog, labels } from './catalog.mjs';
const $=id=>document.getElementById(id);
const money=cents=>new Intl.NumberFormat('pl-PL',{style:'currency',currency:'PLN'}).format(cents/100);
const option=(text,value)=>{const node=document.createElement('option');node.textContent=text;node.value=value;return node;};
function levels(){
  const entry=catalog[$('game').value];
  $('from').replaceChildren(...entry.levels.map(level=>option(labels[level],level)));
  $('to').replaceChildren(...entry.levels.map(level=>option(labels[level],level)));
  $('from').value=entry.levels[0];$('to').value=entry.levels[Math.min(3,entry.levels.length-1)];render();
}
function servers(){const entry=catalog[$('game').value];$('server').replaceChildren(...Object.entries(entry.servers).map(([key,value])=>option(value.label,key)));}
function render(){
  try {
    const result=calculate(catalog,{game:$('game').value,server:$('server').value,from:$('from').value,to:$('to').value,priority:$('priority').checked,streaming:$('streaming').checked});
    $('error').textContent='';$('total').textContent=money(result.total_minor);$('base').textContent=money(result.base_minor);$('extras').textContent=money(result.surcharge_minor);
    $('breakdown').replaceChildren(...result.breakdown.map(step=>{const item=document.createElement('li');item.textContent=`${labels[step.from]} → ${labels[step.to]}: ${money(step.price_minor)}`;return item;}));
    if(result.server_extra_minor){const item=document.createElement('li');item.textContent='Serwer: '+money(result.server_extra_minor);$('breakdown').append(item);}
    $('preview-status').textContent='Wycena demo gotowa. Żadne zamówienie ani płatność nie zostały utworzone.';
  } catch(error) {
    $('error').textContent=error.message;$('total').textContent='—';$('base').textContent='—';$('extras').textContent='—';$('breakdown').replaceChildren();$('preview-status').textContent='Popraw konfigurację.';
  }
}
$('game').replaceChildren(...Object.entries(catalog).map(([key,entry])=>option(entry.label,key)));
$('game').addEventListener('change',()=>{servers();levels();});
for(const id of ['server','from','to','priority','streaming'])$(id).addEventListener('change',render);
$('reset').addEventListener('click',()=>{$('game').value='moba';$('priority').checked=false;$('streaming').checked=false;servers();levels();});
servers();levels();
