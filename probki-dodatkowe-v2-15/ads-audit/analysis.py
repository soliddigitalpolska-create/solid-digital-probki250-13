import csv, pathlib, unittest
def ratio(n,d): return None if not d else round(float(n)/float(d),4)
rows=list(csv.DictReader((pathlib.Path(__file__).parent/'sample-data.csv').open(encoding='utf-8')))
cost=sum(float(r['cost']) for r in rows); orders=sum(int(r['orders']) for r in rows)
assert cost==4140 and orders==162 and len(rows)==18
assert ratio(190,0) is None
print({'cost':cost,'orders':orders,'cost_per_order':ratio(cost,orders),'own_fictional_data':True})
