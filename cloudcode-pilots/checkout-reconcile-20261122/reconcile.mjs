export function money(value, field) {
  if (typeof value !== 'string' || !/^\d{1,9}(\.\d{1,2})?$/.test(value)) {
    throw new Error(`${field}: podaj nieujemną kwotę jako tekst, np. 129.00`);
  }
  const [whole, fraction=''] = value.split('.');
  return Number(whole)*100+Number(fraction.padEnd(2,'0'));
}

export function reconcile(input) {
  const errors=[], warnings=[];
  try {
    if (!input || typeof input!=='object' || !input.order || !Array.isArray(input.exports)) throw new Error('Wymagane: order oraz tablica exports.');
    const o=input.order;
    if (typeof o.id!=='string'||!o.id.trim()||o.id.length>80) throw new Error('Nieprawidłowy identyfikator zamówienia.');
    if(typeof o.currency!=='string'||!['PLN','EUR','USD','GBP'].includes(o.currency)) throw new Error('Nieobsługiwana lub brakująca waluta.');
    if(!Array.isArray(o.items)||o.items.length===0||o.items.length>100) throw new Error('Podaj od 1 do 100 pozycji.');
    let itemTotal=0;
    for(const [i,item] of o.items.entries()) {
      if(!Number.isSafeInteger(item.quantity)||item.quantity<1||item.quantity>10000) throw new Error(`Pozycja ${i+1}: nieprawidłowa ilość.`);
      itemTotal+=money(item.unitGross,`Pozycja ${i+1}`)*item.quantity;
    }
    if(!Number.isSafeInteger(itemTotal))throw new Error('Przekroczony zakres bezpiecznych obliczeń.');
    const shipping=money(o.shippingGross,'Dostawa'),deposit=money(o.depositGross,'Kaucja'),total=money(o.totalGross,'Suma zamówienia');
    const calculated=itemTotal+shipping+deposit;
    if(calculated!==total)errors.push(`Suma zamówienia różni się o ${((total-calculated)/100).toFixed(2)} ${o.currency} od pozycji + dostawy + kaucji.`);
    const matches=input.exports.filter(x=>x&&x.orderId===o.id);
    if(matches.length!==1)errors.push(matches.length===0?'Brak eksportu z identyfikatorem zamówienia.':'Więcej niż jeden eksport tego zamówienia — sprawdź duplikat.');
    if(matches.length===1){
      const e=matches[0];
      if(e.currency!==o.currency)errors.push('Waluta eksportu różni się od waluty zamówienia.');
      if(money(e.totalGross,'Suma eksportu')!==total)errors.push('Suma eksportu różni się od sumy zamówienia.');
      if(money(e.depositGross,'Kaucja eksportu')!==deposit)errors.push('Kaucja nie została poprawnie przeniesiona do eksportu.');
    }
    if(!o.payment||typeof o.payment.test!=='boolean'||!['pending','authorized','captured','refunded'].includes(o.payment.state))throw new Error('Wymagane jawne payment.test (true/false) i payment.state.');
    if(o.payment.test)warnings.push('Zamówienie testowe — nie traktuj go jako realnej wpłaty.');
    const stateLabels={pending:'Oczekujące',authorized:'Autoryzacja, bez potwierdzenia pobrania',captured:'Pobranie zadeklarowane w danych',refunded:'Zwrot zadeklarowany w danych'};
    if(o.payment.state!=='captured')warnings.push('Brak zadeklarowanego pobrania środków.');
    warnings.push('To kontrola zgodności dostarczonych danych. Nie potwierdza wpłaty w bramce ani wypłaty na rachunek.');
    return {valid:errors.length===0,orderId:o.id,currency:o.currency,calculatedGross:(calculated/100).toFixed(2),reportedGross:(total/100).toFixed(2),paymentState:stateLabels[o.payment.state],test:o.payment.test,evidence:'INPUT_ONLY',errors,warnings};
  }catch(e){return {valid:false,evidence:'INPUT_ONLY',errors:[...errors,e.message],warnings};}
}
