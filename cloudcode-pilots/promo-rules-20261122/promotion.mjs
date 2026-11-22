export function calculate(lines, rule) {
  if (!['two-plus-one','fifth-once','every-fifth'].includes(rule)) throw Error('Nieznana reguła');
  if (!Array.isArray(lines) || !lines.length) throw Error('Brak pozycji');
  let subtotal = 0; const eligible = [];
  for (const l of lines) {
    if (!Number.isSafeInteger(l.priceGrosz) || l.priceGrosz < 1 || l.priceGrosz > 100000000) throw Error('Nieprawidłowa cena');
    if (!Number.isInteger(l.quantity) || l.quantity < 0 || l.quantity > 100) throw Error('Nieprawidłowa liczba sztuk');
    if (typeof l.eligible !== 'boolean') throw Error('Brak kwalifikacji produktu');
    subtotal += l.priceGrosz * l.quantity;
    if (l.eligible) for (let i=0;i<l.quantity;i++) eligible.push(l.priceGrosz);
  }
  if (!Number.isSafeInteger(subtotal) || eligible.length > 1000) throw Error('Koszyk przekracza limit demonstracji');
  eligible.sort((a,b)=>a-b);
  const discounted = rule === 'two-plus-one' ? Math.floor(eligible.length/3) : rule === 'fifth-once' ? Number(eligible.length>=5) : Math.floor(eligible.length/5);
  const discount = eligible.slice(0,discounted).reduce((s,p)=>s+(rule==='two-plus-one'?p:Math.round(p/2)),0);
  return {rule, eligibleUnits:eligible.length, discountedUnits:discounted, subtotalGrosz:subtotal, discountGrosz:discount, totalGrosz:subtotal-discount, currency:'PLN', evidence:'DEMO_ONLY'};
}
