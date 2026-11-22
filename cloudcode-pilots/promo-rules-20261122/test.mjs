import test from 'node:test';
import assert from 'node:assert/strict';
import {calculate as calc} from './promotion.mjs';
const l=(quantity,priceGrosz=10000,eligible=true)=>({quantity,priceGrosz,eligible});
const cases=[
 ['2+1: dwie sztuki bez rabatu',[l(2)],'two-plus-one',20000,0],
 ['2+1: trzecia sztuka gratis',[l(3)],'two-plus-one',20000,10000],
 ['2+1: sześć sztuk',[l(6)],'two-plus-one',40000,20000],
 ['2+1: tańsza sztuka gratis',[l(2,10000),l(1,6000)],'two-plus-one',20000,6000],
 ['Brak sumowania dwóch promocji',[l(5)],'two-plus-one',40000,10000],
 ['Piąta: cztery sztuki',[l(4)],'fifth-once',40000,0],
 ['Piąta: pięć sztuk',[l(5)],'fifth-once',45000,5000],
 ['Piąta: rabat tylko raz przy dziesięciu',[l(10)],'fifth-once',95000,5000],
 ['Każda piąta: dwa rabaty przy dziesięciu',[l(10)],'every-fifth',90000,10000],
 ['Niekwalifikujące produkty bez rabatu',[l(2),l(4,10000,false)],'two-plus-one',60000,0],
 ['Zaokrąglenie połowy 99,99 zł',[l(5,9999)],'fifth-once',44995,5000],
 ['Koszyk zerowy bez rabatu',[l(0)],'two-plus-one',0,0]
];
for(const [name,lines,rule,total,discount] of cases) test(name,()=>{const r=calc(lines,rule);assert.equal(r.totalGrosz,total);assert.equal(r.discountGrosz,discount);assert.equal(r.evidence,'DEMO_ONLY');});
test('Nieznana reguła odrzucona',()=>assert.throws(()=>calc([l(3)],'stack')));
test('Ułamkowa liczba sztuk odrzucona',()=>assert.throws(()=>calc([l(2.5)],'two-plus-one')));
test('Ujemna cena odrzucona',()=>assert.throws(()=>calc([l(3,-2)],'two-plus-one')));
test('Kwota z ułamkiem grosza odrzucona',()=>assert.throws(()=>calc([l(3,100.5)],'two-plus-one')));
test('Brak kwalifikacji odrzucony',()=>assert.throws(()=>calc([{quantity:3,priceGrosz:10000}],'two-plus-one')));
test('Wejście pozostaje bez zmian',()=>{const x=[l(3)];const original=JSON.stringify(x);calc(x,'two-plus-one');assert.equal(JSON.stringify(x),original);});
