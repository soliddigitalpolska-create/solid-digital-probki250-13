const base={order:{id:'DEMO-104',currency:'PLN',items:[{sku:'DEMO-SKU',quantity:1,unitGross:'129.00'}],shippingGross:'14.00',depositGross:'20.00',totalGross:'163.00',payment:{state:'captured',test:false}},exports:[{orderId:'DEMO-104',currency:'PLN',totalGross:'163.00',depositGross:'20.00'}]};
export function fixture(name='ok'){
 const value=structuredClone(base);
 if(name==='deposit')delete value.exports[0].depositGross;
 if(name==='authorized')value.order.payment.state='authorized';
 if(name==='test')value.order.payment.test=true;
 if(name==='duplicate')value.exports.push(structuredClone(value.exports[0]));
 return value;
}
