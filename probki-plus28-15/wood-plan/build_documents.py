import json,csv,shutil,html,hashlib,zipfile,math
from pathlib import Path
from datetime import datetime,timezone
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];WORK=Path(__file__).resolve().parent;OUT=ROOT/'outputs/probki-plus28-2026-10-15/wood-plan'
M=json.loads((OUT/'geometry-manifest.json').read_text(encoding='utf-8'));PARTS=M['parts']
for name,path in [('Regular','C:/Windows/Fonts/arial.ttf'),('Bold','C:/Windows/Fonts/arialbd.ttf')]:pdfmetrics.registerFont(TTFont(name,path))
INK=colors.HexColor('#192d2b');GREEN=colors.HexColor('#326251');GRAY=colors.HexColor('#657470');PALE=colors.HexColor('#f0f3ed');LINE=colors.HexColor('#c7d0c6');WOOD=colors.HexColor('#ebd6b8')
W,H=420*mm,297*mm
C=canvas.Canvas(str(OUT/'wood01-dokumentacja-A3.pdf'),pagesize=(W,H));C.setTitle('WOOD 01 | dokumentacja techniczna regału');C.setAuthor('Solid Digital | własny projekt demonstracyjny')
def text(x,y,s,size=10,bold=False,color=INK):
 C.setFillColor(color);C.setFont('Bold' if bold else 'Regular',size);C.drawString(x,y,s)
def page(n,title,sub):
 C.setFillColor(colors.white);C.rect(0,0,W,H,fill=1,stroke=0);text(38,H-39,'SOLID DIGITAL  /  WŁASNA PRÓBKA WARSZTATOWA',9,True,GREEN);text(38,H-75,title,25,True);text(38,H-98,sub,11,color=GRAY)
 C.setStrokeColor(LINE);C.setLineWidth(.6);C.line(38,40,W-38,40);text(38,24,'WOOD 01  •  Regał 800 × 350 × 600 mm  •  rewizja 01 / 15.10.2026',8,color=GRAY);text(W-165,24,f'A3  /  arkusz {n} z 5',8,color=GRAY)
def imagefit(file,x,y,w,h):
 im=Image.open(OUT/file);iw,ih=im.size;ratio=min(w/iw,h/ih);C.drawImage(ImageReader(im),x+(w-iw*ratio)/2,y+(h-ih*ratio)/2,width=iw*ratio,height=ih*ratio,mask='auto')
def line(x1,y1,x2,y2,color=INK,width=.8):C.setStrokeColor(color);C.setLineWidth(width);C.line(x1,y1,x2,y2)
def dimh(x1,x2,y,yref,label):
 line(x1,yref,x1,y+4,GRAY,.35);line(x2,yref,x2,y+4,GRAY,.35);line(x1,y,x2,y,GRAY,.45)
 for x in [x1,x2]:line(x-2.5,y-2.5,x+2.5,y+2.5,GRAY,.6)
 C.setFont('Regular',9);tw=pdfmetrics.stringWidth(str(label),'Regular',9);C.setFillColor(colors.white);C.rect((x1+x2)/2-tw/2-4,y-2,tw+8,12,fill=1,stroke=0);text((x1+x2)/2-tw/2,y+1,str(label),9,color=GRAY)
def dimv(x,y1,y2,xref,label):
 line(xref,y1,x-4,y1,GRAY,.35);line(xref,y2,x-4,y2,GRAY,.35);line(x,y1,x,y2,GRAY,.45)
 for y in [y1,y2]:line(x-2.5,y-2.5,x+2.5,y+2.5,GRAY,.6)
 C.saveState();C.translate(x-5,(y1+y2)/2);C.rotate(90);C.setFillColor(colors.white);tw=pdfmetrics.stringWidth(str(label),'Regular',9);C.rect(-tw/2-4,-2,tw+8,12,fill=1,stroke=0);text(-tw/2,1,str(label),9,color=GRAY);C.restoreState()
def table(x,y,width,headers,rows,colfracs):
 C.setFillColor(PALE);C.rect(x,y-28,width,28,fill=1,stroke=0);cols=[x];
 for f in colfracs[:-1]:cols.append(cols[-1]+width*f)
 for xx,h in zip(cols,headers):text(xx+9,y-18,h,9,True)
 y-=28
 for row in rows:
  for xx,s in zip(cols,row):text(xx+9,y-21,str(s),10)
  line(x,y-32,x+width,y-32,LINE,.4);y-=32
 return y

# 1 - hero, native object and factual scope.
page(1,'WOOD 01. Czytelny projekt, od modelu do montażu.','Własny regał demonstracyjny. Wszystkie widoki powstają z jednej, parametrycznej geometrii.')
imagefit('01-regal-zlozony.png',35,160,720,540)
text(800,660,'800 × 350 × 600',28,True);text(800,635,'szerokość × głębokość × wysokość [mm]',10,color=GRAY)
for yy,a,b in [(580,'6 elementów','sklejka brzozowa, grubość 18 mm'),(510,'16 połączeń','wkręty 4 × 40; osie pilota Ø3'),(440,'1.06176 m²','łączna powierzchnia gotowych elementów'),(370,'Natywny model','Blender 5.2.2 + eksport GLB')]:
 text(800,yy,a,18,True,GREEN);text(800,yy-22,b,10,color=GRAY)
text(65,125,'Zawartość: rzuty 1:5, wymiary, lista cięcia, rozstrzelony widok, kolejność montażu i szablon osi połączeń.',12)
text(65,103,'To rzeczywiście wykonany projekt własny. Nie przedstawia realizacji klienta ani wyniku fizycznego testu mebla.',10,color=GRAY)
C.showPage()

# 2 - scaled vector orthographic views, generated from the same component data.
page(2,'Rzuty i wymiary.','Jednostka: mm. Skala rzutów 1:5 przy wydruku A3 w 100%. Wymiary liczbowe są nadrzędne.')
scale=mm/5
def projection(ax1,ax2,ox,oy,label,hidden=False):
 text(ox,oy+620*scale+22,label,12,True)
 for d in PARTS:
  x=(d['center_mm'][ax1]-d['size_mm'][ax1]/2);y=(d['center_mm'][ax2]-d['size_mm'][ax2]/2)
  if ax1==0:x+=400
  if ax1==1:x+=175
  if ax2==1:y+=175
  C.setStrokeColor(INK);C.setFillColor(WOOD);C.setLineWidth(.65)
  if hidden:C.setDash(3,2)
  C.rect(ox+x*scale,oy+y*scale,d['size_mm'][ax1]*scale,d['size_mm'][ax2]*scale,fill=0,stroke=1);C.setDash()
frontx,fronty=84,330;projection(0,2,frontx,fronty,'01  Z przodu')
dimh(frontx,frontx+800*scale,fronty-30,fronty,'800');dimv(frontx-32,fronty,fronty+600*scale,frontx,'600')
dimh(frontx+18*scale,frontx+782*scale,fronty+620*scale,fronty+600*scale,'764 - światło między bokami')
dimv(frontx+800*scale+24,fronty+118*scale,fronty+550*scale,frontx+800*scale,'432 - prześwit')
text(710,260,'Spód półek: z = 100 i z = 550.',10,color=GRAY)
sidex,sidey=710,330;projection(1,2,sidex,sidey,'02  Z boku (krawędzie wewnętrzne)',True)
dimh(sidex,sidex+350*scale,sidey-30,sidey,'350');dimv(sidex+350*scale+28,sidey,sidey+600*scale,sidex+350*scale,'600')
topx,topy=84,83
for d in PARTS:
 x=d['center_mm'][0]-d['size_mm'][0]/2+400;y=d['center_mm'][1]-d['size_mm'][1]/2+175
 C.setStrokeColor(INK);C.setLineWidth(.65);C.rect(topx+x*scale,topy+y*scale,d['size_mm'][0]*scale,d['size_mm'][1]*scale,fill=0,stroke=1)
text(570,180,'03  Z góry',12,True);text(570,155,'Wszystkie płyty: 18 mm.',10);text(570,135,'Rygle C: przy tylnej krawędzi; 70 mm wysokości.',10);text(570,115,'Krawędzie widoczne: zaokrąglenie 0.6 mm w modelu.',10)
C.showPage()

# 3 - actual exploded source render, all part IDs and exact cut sizes.
page(3,'Rozstrzelenie i lista elementów.','Identyfikatory A/B/C są zapisane również jako nazwy obiektów w pliku Blender.')
imagefit('02-widok-rozstrzelony.png',35,120,740,590)
rows=[['A','Boki',2,'600 × 350 × 18'],['B','Półki',2,'764 × 350 × 18'],['C','Rygle tylne',2,'764 × 70 × 18']]
table(770,650,375,['ID','Element','Szt.','Dł. × szer. × gr.'],rows,[.10,.30,.12,.48])
text(785,460,'A1 / A2',13,True,GREEN);text(785,439,'Lewy i prawy bok - elementy lustrzane.',10)
text(785,395,'B1 / B2',13,True,GREEN);text(785,374,'Półki dolna i górna - identyczny rozkrój.',10)
text(785,330,'C1 / C2',13,True,GREEN);text(785,309,'Rygle dolny i górny - identyczny rozkrój.',10)
text(785,247,'Łączniki: 16 × wkręt 4 × 40 mm.',11,True)
text(785,223,'Wymiary elementów po cięciu, w milimetrach.',9,color=GRAY)
text(785,204,'Rzaz piły uwzględnić poza wymiarem elementu.',9,color=GRAY)
text(60,91,'Źródła: geometria edytowalna .blend, podgląd .glb, rysunki wektorowe .svg i lista elementów .csv.',11)
C.showPage()

# 4 - real geometry in four actual assembly states.
page(4,'Montaż w czterech krokach.','Rygiel dolny: z = 30–100. Rygiel górny: z = 480–550. Półki opierają się na ich górnych krawędziach.')
steps=[('01','Boki + rygle','Ustaw rygle C między bokami A. Złap osie połączeń i sprawdź kąty.'),('02','Dolna półka','Umieść B1: dolna powierzchnia 100 mm nad podstawą boków.'),('03','Górna półka','Umieść B2: dolna powierzchnia 550 mm nad podstawą boków.'),('04','Połączenia i kontrola','Wykonaj połączenia; porównaj przekątne i wymiary końcowe.')]
for idx,(num,title,desc) in enumerate(steps):
 x=45+(idx%2)*560;y=400 if idx<2 else 75
 C.setFillColor(PALE);C.roundRect(x,y,540,305,8,fill=1,stroke=0);imagefit(f'etap-{idx+1}.png',x+15,y+55,510,240);text(x+18,y+38,num+'  '+title,14,True);text(x+18,y+18,desc,8.5,color=GRAY)
C.showPage()

# 5 - manufacturing positions in a local coordinate convention and cut layout.
page(5,'Połączenia i rozkrój.','Szablon osi boków A1/A2. Początek: lewy dolny narożnik w widoku boku, y od przedniej krawędzi.')
ox,oy=85,290;sc=mm/4
C.setStrokeColor(INK);C.rect(ox,oy,350*sc,600*sc,fill=0,stroke=1)
localholes=[(h['y_mm']+175,h['z_mm']) for h in M['pilot_axes'] if h['side']==1]
for i,(y,z) in enumerate(localholes,1):
 x1,y1=ox+y*sc,oy+z*sc;C.setFillColor(GREEN);C.circle(x1,y1,2.1,fill=1,stroke=0);line(x1-5,y1,x1+5,y1,GREEN,.4);line(x1,y1-5,x1,y1+5,GREEN,.4);text(x1+7,y1+4,str(i),8,True,GREEN)
dimh(ox,ox+350*sc,oy-26,oy,'350');dimv(ox-30,oy,oy+600*sc,ox,'600')
text(70,240,'8 osi na każdy bok / 16 łącznie. Oś pilota Ø3, wkręt 4 × 40.',10,True)
text(70,220,'Rozstaw otworów półek: 230; margines od przodu i tyłu: 60.',10)
text(70,200,'Osie rygli: 9 mm od tylnej krawędzi; 15 i 55 od ich dołu.',10)
table(450,690,640,['Nr','y od przodu','z od dołu','Element'],[[i+1,y,z,'B1' if z==109 else 'B2' if z==559 else 'C1' if z<100 else 'C2'] for i,(y,z) in enumerate(localholes)],[.12,.25,.25,.38])
text(450,390,'Plan rozkroju: płyta 2440 × 1220, rzaz 3 mm',13,True)
sx,sy,ss=450,75,.25
C.setFillColor(PALE);C.setStrokeColor(GRAY);C.rect(sx,sy,2440*ss,1220*ss,fill=1,stroke=1)
nest=[('A1',0,0,600,350),('A2',603,0,600,350),('B1',1206,0,764,350),('B2',0,353,764,350),('C1',767,353,764,70),('C2',767,426,764,70)]
for id,x,y,w,h in nest:
 C.setFillColor(WOOD);C.setStrokeColor(GRAY);C.rect(sx+x*ss,sy+y*ss,w*ss,h*ss,fill=1,stroke=1);text(sx+x*ss+6,sy+y*ss+6,id,9,True)
text(70,150,'Materiały źródłowe zawierają osie pilota jako osobną kolekcję',10,color=GRAY);text(70,133,'DRILL_GUIDES. To rzeczywista geometria pomocnicza,',10,color=GRAY);text(70,116,'domyślnie ukryta w renderze; płyty pozostają edytowalne.',10,color=GRAY)
C.showPage();C.save()

# Machine-readable, UTF-8 cut list: no quantities hidden in prose.
with (OUT/'cut-list.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f,delimiter=';');writer.writerow(['ID','Nazwa','Sztuki','Dlugosc_mm','Szerokosc_mm','Grubosc_mm','Material'])
 for d in PARTS:writer.writerow([d['id'],d['name'],1,*d['cut_mm'],'Sklejka brzozowa'])
with (OUT/'pilot-axes.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f,delimiter=';');writer.writerow(['Bok','Element_docelowy','y_od_przodu_mm','z_od_dolu_mm','Pilot_mm'])
 for h in M['pilot_axes']:writer.writerow(['A1' if h['side']<0 else 'A2',h['target'],h['y_mm']+175,h['z_mm'],3])

# Editable SVG projections use original dimensions, not traced render pixels.
for label,axes in [('front',(0,2)),('side',(1,2)),('top',(0,1))]:
 ax,ay=axes;bw=[800,350,600][ax];bh=[800,350,600][ay];svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{bw+140}mm" height="{bh+140}mm" viewBox="-70 -70 {bw+140} {bh+140}">','<rect x="-70" y="-70" width="100%" height="100%" fill="white"/>',f'<text x="0" y="-35" font-size="16" font-family="Arial">WOOD 01 / {label} / mm / 1:1</text>']
 for d in PARTS:
  x=d['center_mm'][ax]-d['size_mm'][ax]/2+([400,175,0][ax]);y=bh-(d['center_mm'][ay]+d['size_mm'][ay]/2+([400,175,0][ay]));svg.append(f'<rect x="{x}" y="{y}" width="{d["size_mm"][ax]}" height="{d["size_mm"][ay]}" fill="none" stroke="#192d2b" stroke-width="1" data-part="{d["id"]}"/>')
 svg.extend([f'<path d="M0 {bh+25} H{bw} M0 {bh+15} V{bh+35} M{bw} {bh+15} V{bh+35}" fill="none" stroke="#326251"/>',f'<text x="{bw/2}" y="{bh+48}" text-anchor="middle" font-size="16" font-family="Arial">{bw}</text>',f'<path d="M{bw+25} 0 V{bh} M{bw+15} 0 H{bw+35} M{bw+15} {bh} H{bw+35}" fill="none" stroke="#326251"/>',f'<text x="{bw+33}" y="{bh/2}" font-size="16" font-family="Arial">{bh}</text>','</svg>'])
 (OUT/f'wood01-{label}.svg').write_text('\n'.join(svg),encoding='utf-8')
for f in ['build_native.py','build_documents.py','verify_native.py']:shutil.copy2(WORK/f,OUT/f)
(OUT/'README.txt').write_text('WOOD 01 - własny projekt demonstracyjny\nRegał 800 x 350 x 600 mm, sklejka brzozowa18 mm,6elementów.\nPDF:5arkuszyA3. Druk100% daje rzuty1:5 na arkuszu2. SVG mają układ1:1.\nBLEND:6nazwanych elementówA1-C2, proceduralny materiał,16wkrętów i osobna ukryta kolekcja osi pilota. Model zawiera osie pomocnicze, nie modelowane gwinty/otwory produkcyjne.\nCSV:gotowe wymiarypo cięciu. Rzaz3mm poza gotowymi wymiarami.\nGLB:geometria i kolor bazowy, bez wypalonego proceduralnego usłojenia. Pełny shader wBLEND.\nNativeQA:ponowneotwarcie/render, wymiary, styki, brakprzecięćpaneli, osiepołączeń i reimportGLB.\nPróbka dokumentacji własnej; nie caseklienta ani fizycznytestobciążenia.\n',encoding='utf-8')
print('PDF, CSV, SVG sources written')
