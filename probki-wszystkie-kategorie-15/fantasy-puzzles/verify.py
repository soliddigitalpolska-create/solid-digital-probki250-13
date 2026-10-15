import pathlib,json,hashlib,zipfile,re,datetime
from PIL import Image
B=pathlib.Path(__file__).resolve().parent
rows=[]
for fn in ['01-miasto-drzewo.png','02-port-powietrzny.png']:
    p=B/fn
    with Image.open(p) as im:
        width,height=im.size
        fmt,mode=im.format,im.mode
        im.verify()
    rows.append(dict(file=fn,width=width,height=height,format=fmt,mode=mode,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),native_unmodified_tool_output=True))
assert all(r['width']==1536 and r['height']==1024 and r['format']=='PNG' for r in rows)
qa=dict(created='2026-10-15',mode='built-in image_gen; one call per image; no private input images',images=rows,visual_review=dict(performed=True,tree_city='Dense coherent tree-city, differentiated foreground/bridges/greenhouses/market, no large blank sky; small distant humans are illustrative detail rather than identity-accurate portraits.',aerial_port='Distinct cool-toned skyport with large blue vessel, white stone terraces and red awnings; water/sky broken by vessels and architecture.',passed_concept_composition=True),print_status='Portfolio concept only. Native1536x1024; not4K, not proofed CMYK and not approved for production printing. Exact final output must be agreed before funding.',external_writes_or_publication=False)
(B/'qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(B/'fantasy-puzzles-native.zip','w',zipfile.ZIP_DEFLATED) as z:
    for fn in ['01-miasto-drzewo.png','02-port-powietrzny.png','prompts.json','qa.json']:
        z.write(B/fn,fn)
html=(B/'index.html').read_text(encoding='utf-8')
refs=set(re.findall(r'(?:href|src)="([^"]+)"',html))
assert all((B/r).is_file() for r in refs if not r.startswith(('http','#','mailto:')))
assert len(rows)==2
print(json.dumps(dict(images=rows,local_html_links=len(refs),zip_bytes=(B/'fantasy-puzzles-native.zip').stat().st_size,publication=False),ensure_ascii=False))
