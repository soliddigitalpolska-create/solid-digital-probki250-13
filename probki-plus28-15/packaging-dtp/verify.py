from pathlib import Path
import sys,json,subprocess,hashlib,zipfile,copy,math,html,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'work/useme-plus28-2026-10-15/pdf-inspect-deps'))
import pikepdf
from PIL import Image,ImageDraw,ImageFont,ImageStat
import build
OUT=build.OUT
N=pikepdf.Name;A=pikepdf.Array;D=pikepdf.Dictionary
process=('C','M','Y','K')
def inspect_and_prune(path):
 result=[]
 with pikepdf.open(path) as pdf:
  for number,page in enumerate(pdf.pages,1):
   spaces={str(k):str(v[1]) for k,v in page.Resources.get('/ColorSpace',{}).items() if isinstance(v,pikepdf.Array) and str(v[0])=='/Separation'}
   states=page.Resources.get('/ExtGState',{});state={'fill':('GRAY',[0]),'stroke':('GRAY',[0]),'op':False,'OP':False,'OPM':0};stack=[];paints=[];rgb=0;textops=0;filtered=[]
   for operands,operator in pikepdf.parse_content_stream(page):
    op=str(operator);vals=list(operands)
    if op in ('Tj','TJ',"'",'"'):textops+=1
    if op in ('BT','ET','Tf','TL'):continue
    filtered.append((operands,operator))
    if op=='q':stack.append(copy.deepcopy(state))
    elif op=='Q':state=stack.pop()
    elif op=='k':state['fill']=('CMYK',[float(x) for x in vals])
    elif op=='K':state['stroke']=('CMYK',[float(x) for x in vals])
    elif op=='g':state['fill']=('GRAY',[float(vals[0])])
    elif op=='G':state['stroke']=('GRAY',[float(vals[0])])
    elif op in ('rg','RG'):rgb+=1
    elif op=='cs':state['fill']=(spaces.get(str(vals[0]),str(vals[0])),[])
    elif op=='CS':state['stroke']=(spaces.get(str(vals[0]),str(vals[0])),[])
    elif op in ('scn','sc'):state['fill']=(state['fill'][0],[float(x) for x in vals])
    elif op in ('SCN','SC'):state['stroke']=(state['stroke'][0],[float(x) for x in vals])
    elif op=='gs':
     st=states.get(vals[0],{})
     for key in ('op','OP','OPM'):
      if '/'+key in st:state[key]=bool(st['/'+key]) if key!='OPM' else int(st['/'+key])
    elif op in ('f','f*','F','B','B*','b','b*') and state['fill'][0]=='/WHITE':paints.append({'kind':'fill','overprint':state['op'],'OPM':state['OPM'],'tint':state['fill'][1]})
   assert textops==0,(path.name,'text not outlined')
   assert rgb==0,(path.name,'RGB paint operators present')
   for paint in paints:assert paint['overprint'] and paint['OPM']==1 and paint['tint']==[1.0],paint
   page.Contents=pdf.make_stream(pikepdf.unparse_content_stream(filtered))
   if '/Font' in page.Resources:del page.Resources['/Font']
   result.append({'page':number,'media_box_pt':[float(x) for x in page.MediaBox],'trim_box_pt':[float(x) for x in page.TrimBox],'bleed_box_pt':[float(x) for x in page.BleedBox],'spot_names':list(spaces.values()),'white_paints':paints,'RGB_paint_operators':rgb,'text_paint_operators':textops,'embedded_raster_xobjects':len(page.Resources.get('/XObject',{}))})
  temp=path.with_suffix('.tmp');pdf.save(temp,min_version='1.7')
 temp.replace(path)
 return result

def plate_ops(page,plate):
 spaces={str(k):str(v[1]).lstrip('/') for k,v in page.Resources.get('/ColorSpace',{}).items() if isinstance(v,pikepdf.Array) and str(v[0])=='/Separation'}
 states=page.Resources.get('/ExtGState',{});state={'fill':('GRAY',[0]),'stroke':('GRAY',[0]),'op':False,'OP':False};stack=[];output=[]
 def emit(op,args=()):output.append((list(args),pikepdf.Operator(op)))
 def cov(color,overprint):
  space,values=color
  if space=='CMYK':return values[process.index(plate)] if plate in process else None
  if space=='GRAY':return 1-values[0] if plate=='K' else (0 if plate in process else None)
  if space==plate:return values[0] if values else 1
  return None if overprint else (0 if plate in process else None)
 for operands,operator in pikepdf.parse_content_stream(page):
  op=str(operator);v=list(operands)
  if op=='q':stack.append(copy.deepcopy(state));emit(op,v)
  elif op=='Q':state=stack.pop();emit(op,v)
  elif op=='k':state['fill']=('CMYK',[float(x) for x in v])
  elif op=='K':state['stroke']=('CMYK',[float(x) for x in v])
  elif op=='g':state['fill']=('GRAY',[float(v[0])])
  elif op=='G':state['stroke']=('GRAY',[float(v[0])])
  elif op=='cs':state['fill']=(spaces.get(str(v[0]),str(v[0])),[])
  elif op=='CS':state['stroke']=(spaces.get(str(v[0]),str(v[0])),[])
  elif op in ('sc','scn'):state['fill']=(state['fill'][0],[float(x) for x in v])
  elif op in ('SC','SCN'):state['stroke']=(state['stroke'][0],[float(x) for x in v])
  elif op=='gs':
   st=states.get(v[0],{})
   for key in ('op','OP'):
    if '/'+key in st:state[key]=bool(st['/'+key])
  elif op in ('f','f*','F','S','s','B','B*','b','b*'):
   fill=op in ('f','f*','F','B','B*','b','b*');stroke=op in ('S','s','B','B*','b','b*');fc=cov(state['fill'],state['op']) if fill else None;sc=cov(state['stroke'],state['OP']) if stroke else None
   if fc is None and sc is None:emit('n');continue
   if op in ('s','b','b*'):emit('h')
   if fc is not None:emit('g',[1-fc])
   if sc is not None:emit('G',[1-sc])
   emit(('B*' if '*' in op else 'B') if fc is not None and sc is not None else ('f*' if '*' in op else 'f') if fc is not None else 'S')
  elif op in ('rg','RG'):raise AssertionError('Unexpected RGB')
  elif op in ('BT','ET','Tf','TL','BMC','BDC','EMC'):continue
  else:emit(op,v)
 return pikepdf.unparse_content_stream(output)

def extract(path,plates,target):
 with pikepdf.open(path) as src:
  dst=pikepdf.Pdf.new()
  for plate in plates:
   for page in src.pages:
    dst.pages.append(page);p=dst.pages[-1];p.Contents=dst.make_stream(plate_ops(page,plate));p.Resources=D();p['/PlateName']=pikepdf.String(plate)
  dst.save(target,min_version='1.7')

labels=inspect_and_prune(OUT/'labels-production.pdf');watch=inspect_and_prune(OUT/'watch-production.pdf')
assert len(labels)==5 and len(watch)==8
assert all(len(x['white_paints'])==1 for x in labels)
for page in labels:
 trim=page['trim_box_pt'];media=page['media_box_pt'];assert abs((trim[2]-trim[0])/build.mm-155)<.001 and abs((trim[3]-trim[1])/build.mm-60)<.001;assert abs(trim[0]/build.mm-3)<.001
assert all(x['embedded_raster_xobjects']==0 for x in labels+watch)
for plate in ['WHITE','C','M','Y','K']:extract(OUT/'labels-production.pdf',[plate],OUT/f'labels-plate-{plate}.pdf')
extract(OUT/'watch-production.pdf',['DIELINE','CREASE','VARNISH'],OUT/'watch-spot-plates.pdf')
data=json.loads((OUT/'source-data.json').read_text(encoding='utf-8'));assert all(x['checksum_valid'] for x in data['labels']['EAN'])
proof={'status':'OWN_TECHNICAL_VECTOR_PROOF_NOT_PRINTED_CUSTOMER_CASE','labels_preflight':labels,'watch_preflight':watch,'white_separation_actual_name':'WHITE','white_color_space':'Separation with DeviceCMYK alternate','white_is_real_spot_not_RGB_simulation':True,'white_paint_effective_fill_overprint':True,'white_effective_OPM':1,'all_visible_text_is_vector_outlines':True,'all_raster_xobjects_zero':True,'process_art_native_DeviceCMYK':True,'plate_method':'Re-read actual production PDF content streams with pikepdf, interpret effective ink and overprint states, isolate actual painted geometry for each ink, then rasterize the derived plate PDFs with Poppler. Plate images are not redrawn from the source design.','white_hole':'Actual compound even-odd WHITE path excludes the same 10 x 5 mm clear window used by process artwork.','not_claimed':['No physical press proof or ISO15416 barcode grade.','No printer-specific ICC/profile or PDF/X certification without supplied print specification.','No paid/customer packaging history or manufactured smartwatch.','No commercial Pantone swatch match or licensed Adobe source file.'],'final_print_conditions':['Approved client texts, regulated label content and assigned product EANs.','Approved printer dieline, material, WHITE/choke/overprint specification and ink order.','Printer profile, output standard, separations and physical proof/acceptance before mass production.']}

sheet=build.Doc('technical-sheet.pdf');sheet.begin(210,297,0);sheet.rect(0,0,210,297,build.PAPER);sheet.text(16,275,'RZECZYWISTY PROOF DTP',23,True,build.NAVY);sheet.text(16,263,'CMYK / WHITE / overprint / wykrojnik',10,False,build.NAVY)
sections=[('01 / Etykiety','Pięć własnych etykiet i autorski znak. Trim 155 x 60 mm, spad 3 mm, choke WHITE 0,15 mm w tej próbce. Wszystkie teksty są krzywymi, geometria jest wektorowa. Kody demonstracyjne mają poprawną cyfrę kontrolną, moduł 0,33 mm i zachowane strefy ciszy; nie są kodami przydzielonymi GS1.'),('02 / Faktyczne farby','Plik produkcyjny zawiera DeviceCMYK oraz nazwany kolor dodatkowy WHITE. Malowanie WHITE ma efektywny overprint fill=true i OPM=1. Osobne płyty C/M/Y/K/WHITE odczytano z tego PDF, a nie narysowano drugi raz do obrazka.'),('03 / Komplet opakowania','Osiem stron: siatka pudełka, wkładka, czterostronicowy skład instrukcji, naklejki ekranu/przewodu/produktu/sticker oraz rysunki przód/bok/tył z brandingiem. Linie DIELINE/CREASE i lakier VARNISH są prawdziwymi kanałami spot.'),('04 / Źródła i uczciwy status','To własne wykonane projekty techniczne, nie opakowania wydrukowane dla klienta. Teksty i model są demonstracyjne. Nie kopiowano załącznika Useme, kodu EAN, logotypu ani treści cudzej marki.'),('05 / Warunki produkcji','Przed finalnym drukiem potrzebne są zatwierdzone treści i numery produktu, siatka drukarni, profil, definicje farb, kolejność druku i standard pliku. Ta próbka nie jest certyfikatem PDF/X, fizycznym proofem ani oceną zgodności produktu.')]
y=243
for title,body in sections:sheet.text(16,y,title,12,True,build.NAVY);y=sheet.para(16,y-9,body,178,9,leading=4.9);y-=13
sheet.text(16,18,'ŹRÓDŁA: NATYWNE WEKTOROWE PDF + SVG + KOD PYTHON + DANE JSON',7,True,build.NAVY);sheet.end();sheet.save();inspect_and_prune(OUT/'technical-sheet.pdf')
(OUT/'preflight.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
poppler=Path('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')
if not poppler.is_file():
 poppler=Path(shutil.which('pdftoppm') or 'pdftoppm')
for file,prefix,dpi in [('labels-production.pdf','label-composite',220),('labels-plate-WHITE.pdf','white-plate',220),('watch-production.pdf','watch-composite',150),('technical-sheet.pdf','technical',120)]:
 subprocess.run([str(poppler),'-png','-overprint','-r',str(dpi),str(OUT/file),str(OUT/prefix)],check=True,capture_output=True)
for plate in process:subprocess.run([str(poppler),'-f','1','-singlefile','-png','-r','150',str(OUT/f'labels-plate-{plate}.pdf'),str(OUT/f'process-plate-{plate}')],check=True,capture_output=True)
white_image=Image.open(OUT/'white-plate-1.png').convert('L');dark=sum(1 for x in white_image.getdata() if x<100);assert dark/len(list(white_image.getdata()))>.85
hole_pixel=white_image.getpixel((round(12/25.4*220),white_image.height-round(8.5/25.4*220)));ink_pixel=white_image.getpixel((round(25/25.4*220),white_image.height-round(8.5/25.4*220)));assert hole_pixel>245 and ink_pixel<60
proof['actual_WHITE_clear_window_pixel_check']={'hole_luminance':hole_pixel,'surrounding_ink_luminance':ink_pixel,'status':'PASS'}
proof['white_plate_raster_dark_fraction']=round(dark/(white_image.width*white_image.height),4);proof['all_9_PDFs_created']=len(list(OUT.glob('*.pdf')))==9
assert proof['all_9_PDFs_created']
(OUT/'preflight.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Full image contact sheets for author inspection; separate source artifact from private client reference.
thumbs=[]
for p in sorted(OUT.glob('label-composite-*.png'))+sorted(OUT.glob('white-plate-*.png')):
 im=Image.open(p).convert('RGB');im.thumbnail((800,330));thumbs.append((p.name,im))
contact=Image.new('RGB',(840,len(thumbs)*365),'#d9dfd8');draw=ImageDraw.Draw(contact)
for j,(name,im) in enumerate(thumbs):draw.text((20,j*365+8),name,fill='black');contact.paste(im,(20,j*365+30))
contact.save(HERE/'labels-contact-sheet.jpg',quality=90)
thumbs=[]
for p in sorted(OUT.glob('watch-composite-*.png')):
 im=Image.open(p).convert('RGB');im.thumbnail((540,650));thumbs.append((p.name,im))
contact=Image.new('RGB',(1140,4*700),'#d9dfd8');draw=ImageDraw.Draw(contact)
for j,(name,im) in enumerate(thumbs):x=20+(j%2)*560;y=20+(j//2)*700;draw.text((x,y),name,fill='black');contact.paste(im,(x,y+25))
contact.save(HERE/'watch-contact-sheet.jpg',quality=90)
print('PREFLIGHT PASS',len(labels),'labels',len(watch),'watch pages','WHITE area',proof['white_plate_raster_dark_fraction'])
