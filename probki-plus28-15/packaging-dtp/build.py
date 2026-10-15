from pathlib import Path
import sys,json,math,html
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE/'tooldeps'))
from reportlab.pdfgen import canvas
from reportlab.lib.colors import CMYKColor,CMYKColorSep
from reportlab.lib.units import mm
from reportlab.graphics.barcode.eanbc import Ean13BarcodeWidget
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
OUT=(HERE if (HERE/'source-data.json').is_file() else ROOT/'outputs/probki-plus28-2026-10-15/packaging-dtp');OUT.mkdir(parents=True,exist_ok=True)
WHITE=CMYKColorSep(0,0,0,0,spotName='WHITE');CUT=CMYKColorSep(0,1,0,0,spotName='DIELINE');FOLD=CMYKColorSep(1,0,0,0,spotName='CREASE');VARNISH=CMYKColorSep(0,0,0,0,spotName='VARNISH')
K=CMYKColor(0,0,0,1);PAPER=CMYKColor(0,0,0,0);NAVY=CMYKColor(.87,.58,.36,.52);CREAM=CMYKColor(.015,.015,.055,0)
FONTS={False:TTFont('C:/Windows/Fonts/arial.ttf'),True:TTFont('C:/Windows/Fonts/arialbd.ttf')}

class GlyphPen(BasePen):
 def __init__(self,glyphset):super().__init__(glyphset);self.path=[]
 def _moveTo(self,p):self.path.append(('M',p))
 def _lineTo(self,p):self.path.append(('L',p))
 def _curveToOne(self,p1,p2,p3):self.path.append(('C',(*p1,*p2,*p3)))
 def _closePath(self):self.path.append(('Z',()))
 def _endPath(self):pass

class Doc:
 def __init__(self,name):self.name=name;self.c=canvas.Canvas(str(OUT/name),pageCompression=1,pdfVersion=(1,7));self.pages=[];self.page=0
 def begin(self,w,h,bleed=3):
  self.page+=1;self.w=w+bleed*2;self.h=h+bleed*2;self.bleed=bleed;self.svg=[];self.c.setPageSize((self.w*mm,self.h*mm));self.c.setTrimBox((bleed*mm,bleed*mm,(bleed+w)*mm,(bleed+h)*mm));self.c.setBleedBox((0,0,self.w*mm,self.h*mm));self.c.setFillColor(K);self.c.setStrokeColor(K)
 def fill(self,col):self.c.setFillColor(col);self.color=col
 def stroke(self,col,width=.2):self.c.setStrokeColor(col);self.c.setLineWidth(width*mm);self.linecolor=col;self.linewidth=width
 def rgb(self,c):
  if isinstance(c,CMYKColorSep):
   if c.spotName in ['WHITE','VARNISH']:return '#9daeb0'
  return '#%02x%02x%02x'%tuple(int(255*(1-min(1,x+c.black))) for x in (c.cyan,c.magenta,c.yellow))
 def rect(self,x,y,w,h,col,stroke=None,lw=.2):
  self.fill(col);self.c.setLineWidth(lw*mm)
  if stroke:self.c.setStrokeColor(stroke)
  self.c.rect(x*mm,y*mm,w*mm,h*mm,fill=1,stroke=int(stroke is not None));self.svg.append(f'<rect x="{x*mm}" y="{y*mm}" width="{w*mm}" height="{h*mm}" fill="{self.rgb(col)}"'+(f' stroke="{self.rgb(stroke)}" stroke-width="{lw*mm}"' if stroke else '')+'/>')
 def line(self,x1,y1,x2,y2,col=K,lw=.2,dash=None):
  self.stroke(col,lw);self.c.setDash(dash or []);self.c.line(x1*mm,y1*mm,x2*mm,y2*mm);self.c.setDash([]);self.svg.append(f'<path d="M{x1*mm},{y1*mm}L{x2*mm},{y2*mm}" fill="none" stroke="{self.rgb(col)}" stroke-width="{lw*mm}"'+(' stroke-dasharray="3,2"' if dash else '')+'/>')
 def outline(self,x,y,w,h,col=K,lw=.2):
  self.stroke(col,lw);self.c.rect(x*mm,y*mm,w*mm,h*mm,fill=0,stroke=1);self.svg.append(f'<rect x="{x*mm}" y="{y*mm}" width="{w*mm}" height="{h*mm}" fill="none" stroke="{self.rgb(col)}" stroke-width="{lw*mm}"/>')
 def circle(self,x,y,r,col):
  self.fill(col);self.c.circle(x*mm,y*mm,r*mm,fill=1,stroke=0);self.svg.append(f'<circle cx="{x*mm}" cy="{y*mm}" r="{r*mm}" fill="{self.rgb(col)}"/>')
 def text(self,x,y,s,size=9,bold=False,col=K):
  font=FONTS[bold];glyphs=font.getGlyphSet();cmap=font.getBestCmap();scale=size/font['head'].unitsPerEm;advance=0;self.fill(col)
  for char in s:
   name=cmap.get(ord(char),'.notdef');pen=GlyphPen(glyphs);glyphs[name].draw(pen);path=self.c.beginPath();commands=[]
   for op,v in pen.path:
    vals=[v[k]*scale+(x*mm+advance if k%2==0 else y*mm) for k in range(len(v))]
    if op=='M':path.moveTo(*vals)
    elif op=='L':path.lineTo(*vals)
    elif op=='C':path.curveTo(*vals)
    elif op=='Z':path.close()
    commands.append(op+' '.join(f'{a:.4f}' for a in vals))
   self.c.drawPath(path,fill=1,stroke=0);self.svg.append(f'<path d="{" ".join(commands)}" fill="{self.rgb(col)}"/>');advance+=font['hmtx'][name][0]*scale
  return advance/mm
 def width(self,s,size=9,bold=False):
  f=FONTS[bold];cm=f.getBestCmap();return sum(f['hmtx'][cm.get(ord(ch),'.notdef')][0] for ch in s)*size/f['head'].unitsPerEm/mm
 def para(self,x,y,text,width,size=6,leading=None,col=K):
  leading=leading or size*1.35/mm;line=''
  for word in text.split():
   trial=(line+' '+word).strip()
   if self.width(trial,size)>width and line:self.text(x,y,line,size,col=col);y-=leading;line=word
   else:line=trial
  if line:self.text(x,y,line,size,col=col);y-=leading
  return y
 def op(self,on):self.c.setFillOverprint(on);self.c.setStrokeOverprint(on);self.c.setOverprintMask(1 if on else 0)
 def end(self):
  svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}mm" height="{self.h}mm" viewBox="0 0 {self.w*mm} {self.h*mm}"><title>Autorska próbka, źródło wektorowe</title><g transform="translate(0,{self.h*mm}) scale(1,-1)">'+''.join(self.svg)+'</g></svg>'
  path=OUT/f'{Path(self.name).stem}-{self.page:02d}.svg';path.write_text(svg,encoding='utf-8');self.pages.append({'page':self.page,'svg':path.name,'media_mm':[self.w,self.h],'bleed_mm':self.bleed});self.c.showPage()
 def save(self):self.c.save()

def logo(d,x,y,size=10,col=NAVY):
 d.circle(x,y,1.7,col);d.rect(x-.5,y-2.4,1,4.8,PAPER);d.rect(x-2.4,y-.5,4.8,1,PAPER);d.text(x+3.8,y-1.25,'FORMA',size,True,col)

def watch_drawing(d,x,y,w=24,h=28):
 d.rect(x+w*.32,y-h*.3,w*.36,h*1.6,CREAM);d.outline(x+w*.32,y-h*.3,w*.36,h*1.6,NAVY,.2);d.rect(x,y,w,h,NAVY);d.rect(x+w*.09,y+h*.09,w*.82,h*.82,PAPER);d.text(x+w*.21,y+h*.51,'09:41',w*.32,True,NAVY);d.text(x+w*.26,y+h*.27,'FORMA',w*.135,True,NAVY);d.rect(x+w,y+h*.55,w*.08,h*.22,CREAM)

def barcode(d,x,y,index):
 # Native EAN-13 bars from ReportLab, extra left quiet zone gives >=11 modules.
 value=f'2000000000{index:02d}';widget=Ean13BarcodeWidget(value,humanReadable=False,barWidth=.33*mm,barHeight=22.85*mm,fontSize=8.5);group=widget.draw();full=value+widget._checkdigit(value)
 d.c.saveState();d.c.translate(x*mm,y*mm);d.c.rotate(90)
 for shape in group.contents:
  if getattr(shape,'fillColor',None) is not None:
   d.c.setFillColor(K);d.c.rect(shape.x+.66*mm,shape.y,shape.width,shape.height,stroke=0,fill=1)
 d.c.restoreState()
 # Record all bar geometry in editable SVG as well, same rotation.
 d.svg.append(f'<g transform="translate({x*mm},{y*mm}) rotate(90)">')
 for shape in group.contents:
  if getattr(shape,'fillColor',None) is not None:d.svg.append(f'<rect x="{shape.x+.66*mm}" y="{shape.y}" width="{shape.width}" height="{shape.height}" fill="#000"/>')
 d.svg.append('</g>')
 d.text(x-24,y-1.5,full,4.3,col=K)
 return {'digits':full,'checksum_valid':widget._checkdigit(full[:12])==full[12],'module_mm':.33,'left_quiet_modules':11,'right_quiet_modules':9,'bar_height_mm':22.85,'meaning':'Own internal demonstration code, not a GS1 allocation or verified print grade'}

palettes=[CMYKColor(.79,.22,.47,.25),CMYKColor(.26,.82,.39,.2),CMYKColor(.37,.23,.88,.22),CMYKColor(.10,.59,.90,.12),CMYKColor(.85,.50,.10,.16)]
labels=Doc('labels-production.pdf');ean=[]
for i,accent in enumerate(palettes,1):
 labels.begin(155,60);b=3
 labels.rect(0,0,161,66,CREAM);labels.rect(49,0,59,66,accent);labels.rect(49,16,59,1.2,PAPER)
 labels.rect(7,6,10,5,PAPER) # clear window: no process ink and no white underprint
 logo(labels,78,56,11,PAPER)
 labels.text(56,43,'FORMUŁA',10,True,PAPER);labels.text(56,28,f'{i:02d}',36,True,PAPER)
 labels.text(56,11,'60 kapsułek',8,True,PAPER);labels.text(56,7,'SUPLEMENT DIETY / DEMO',4.1,False,PAPER)
 ean.append(barcode(labels,29,14,i));labels.text(5,57,'PRÓBKA DTP',5.5,True)
 labels.para(31,54,'Własny układ demonstracyjny. Nie jest produktem handlowym.',14,4.2)
 labels.para(31,35,'Składy, zalecenia oraz dane producenta w zleceniu dostarcza i zatwierdza klient.',14,4.2)
 labels.text(110,56,'FORMA / SERIA 01-05',6,True,accent)
 y=labels.para(110,50,'Projekt do oceny typografii, systemu kolorów i rozbarwień. Nazwy nie opisują produktu przeznaczonego do spożycia.',44,5.3)
 labels.line(110,y-1,154,y-1,accent,.18)
 labels.text(110,y-6,'KONTROLA UKŁADU',5.8,True,accent)
 labels.para(110,y-10,'Wektorowy druk CMYK. Osobny poddruk WHITE. Format po obcięciu 155 x 60 mm. Spad 3 mm. Teksty w krzywych.',44,5.1)
 labels.text(110,8,f'ARTWORK DEMO / F-{i:02d}',4.5,True)
 # WHITE is a genuine named Separation applied LAST with real fill/stroke overprint.
 labels.op(True);labels.fill(WHITE);path=labels.c.beginPath();path.rect(.15*mm,.15*mm,160.7*mm,65.7*mm);path.rect(7*mm,6*mm,10*mm,5*mm);labels.c.drawPath(path,fill=1,stroke=0,fillMode=0);labels.op(False)
 # SVG is a composite source only; production WHITE is authoritative in the PDF.
 labels.end()
labels.save()

watch=Doc('watch-production.pdf')
# Straight tuck demonstrator: 45 x 70 x 20 mm, 12 mm glue tab.
watch.begin(158,126,3);watch.rect(0,0,164,132,PAPER)
x0,y0=11,31;panels=[(45,'FRONT'),(20,'BOK'),(45,'TYŁ'),(20,'BOK'),(12,'KLEJ')];x=x0
for n,(width,name) in enumerate(panels):
 if n<4:watch.rect(x,y0,width,70,NAVY if n in (0,2) else CREAM)
 if n==0:
  logo(watch,x+9,y0+60,10,PAPER);watch.text(x+6,y0+45,'S1',27,True,PAPER);watch_drawing(watch,x+13,y0+17,20,23);watch.text(x+6,y0+8,'MODEL KONCEPCYJNY',4.6,True,PAPER)
 elif n==2:
  watch.para(x+4,y0+60,'FORMA S1 to własny model graficzny do oceny kompletu opakowania, instrukcji i oznaczeń.',width-8,6.5,col=PAPER);watch.para(x+4,y0+30,'Nie jest produktem handlowym. Brak deklaracji CE, parametrów sprzętu i wyników badań.',width-8,5.5,col=PAPER)
 elif n<4:watch.text(x+4,y0+57,'FORMA',6.5,True);watch.text(x+4,y0+9,'S1 / DEMO',4.5)
 if n<4:
  flap=20 if n in (0,2) else 16
  watch.rect(x,y0+70,width,flap,CREAM);watch.rect(x,y0-flap,width,flap,CREAM)
  watch.op(True)
  for y in [y0-flap,y0+70+flap]:watch.line(x,y,x+width,y,CUT,.15)
  for y1,y2 in [(y0-flap,y0),(y0+70,y0+70+flap)]:watch.line(x,y1,x,y2,CUT,.15);watch.line(x+width,y1,x+width,y2,CUT,.15)
  for y in [y0,y0+70]:watch.line(x,y,x+width,y,FOLD,.15,[3,2])
  watch.op(False)
 x+=width
watch.op(True);watch.line(x0,y0,x0,y0+70,CUT,.15);watch.line(x,y0,x,y0+70,CUT,.15);watch.line(x-12,y0,x,y0,CUT,.15);watch.line(x-12,y0+70,x,y0+70,CUT,.15)
for px in [x0+45,x0+65,x0+110,x0+130]:watch.line(px,y0,px,y0+70,FOLD,.15,[3,2])
# A genuine spot-varnish logo patch. Neutral alternate, overprint on process artwork.
watch.fill(VARNISH);watch.c.rect((x0+4)*mm,(y0+51)*mm,37*mm,16*mm,fill=1,stroke=0);watch.op(False)
watch.text(11,11,'SIATKA WŁASNA / 45 x 70 x 20 mm / KLEJ 12 mm',6,True);watch.text(11,7,'Geometria do demonstracji DTP, bez deklaracji zatwierdzenia introligatorni.',4.8);watch.end()

# Matching insert with strap slots and retention opening.
watch.begin(80,104,3);watch.rect(0,0,86,110,PAPER);watch.rect(14,20,43,67,CREAM);watch.text(17,79,'WKŁADKA S1',7,True)
watch.op(True)
for x1,y1,x2,y2 in [(14,20,57,20),(57,20,57,87),(57,87,14,87),(14,87,14,20)]:watch.line(x1,y1,x2,y2,CUT,.15)
watch.outline(16.5,31.5,38,44,CUT,.15)
for yy in [24,82]:watch.outline(21.5,yy,28,2,CUT,.15)
watch.op(False);watch.text(14,12,'43 x 67 mm / otwór 38 x 44 / sloty 28 x 2',5.4);watch.text(14,7,'Weryfikacja dopasowania na makiecie fizycznej przed produkcją.',4.7);watch.end()

manual=[('FORMA S1','Przewodnik po modelu','Ilustracyjny model do oceny przygotowania opakowania. Oznaczenia, tekst i rysunki są własne; nie opisują wyprodukowanego urządzenia.'),('Elementy modelu','Czytelny schemat części','01 Ekran. 02 Przycisk POWER. 03 Pasek. 04 Sprzączka. Każde oznaczenie ma tę samą nazwę na rysunkach, naklejkach i opakowaniu.'),('Dopasowanie paska','Trzy kroki na jednej planszy','01 Przełóż pasek przez sprzączkę. 02 Wybierz otwór i zamknij zapięcie. 03 Przeprowadź końcówkę przez szlufkę. Rysunek pokazuje kolejność dla własnego modelu koncepcyjnego.'),('Przed przekazaniem do druku','Jedna zaakceptowana wersja','Producent zatwierdza fakty, ostrzeżenia i działanie przycisków. Skład DTP porządkuje tekst, diagramy i wersje językowe; nie zastępuje dokumentacji technicznej urządzenia.')]
for idx,(title,subtitle,body) in enumerate(manual,1):
 watch.begin(90,65,3);watch.rect(0,0,96,71,CREAM);watch.rect(0,56,96,15,NAVY);watch.text(8,62,title,11,True,PAPER);watch.text(8,49,subtitle,9,True);watch.para(8,41,body,45 if idx in (1,2) else 77,6.7)
 if idx in (1,2):
  watch_drawing(watch,66,23,14,17)
  if idx==2:
   for xx,yy,n in [(63,40,'01'),(84,33,'02'),(69,17,'03')]:watch.circle(xx,yy,2.1,NAVY);watch.text(xx-1.2,yy-.8,n,4.6,True,PAPER)
 elif idx==3:
  for xx,n in [(12,'01'),(38,'02'),(64,'03')]:watch.rect(xx,17,18,7,NAVY);watch.text(xx+6,19,n,7,True,PAPER)
 elif idx==4:
  watch.outline(8,17,77,6,NAVY,.2);watch.text(11,19,'TEKST / DIAGRAM / WERSJA / DATA AKCEPTACJI',5.3,True,NAVY)
 watch.line(8,13,86,13,NAVY,.2);watch.text(8,8,'AUTORSKI SKŁAD / PRÓBKA TECHNICZNA',4.8);watch.text(80,8,f'{idx}/4',5.5,True);watch.end()

# Actual cut-line artwork for all small product marks.
watch.begin(148,210,3);watch.rect(0,0,154,216,PAPER);watch.text(10,200,'S1 / OZNACZENIA I NAKLEJKI',13,True)
items=[(12,135,40,46,'FOLIA / EKRAN'),(70,156,45,14,'PRZEWÓD'),(70,129,45,14,'ETYKIETA S1'),(12,88,40,25,'FORMA'),(70,88,40,25,'S1 / STICKER')]
for xx,yy,ww,hh,title in items:
 watch.rect(xx,yy,ww,hh,NAVY if title in ('PRZEWÓD','FORMA') else CREAM)
 if title=='FOLIA / EKRAN':
  watch.rect(xx,yy+hh-10,ww,10,NAVY);watch.text(xx+4,yy+hh-6,'FORMA S1',7,True,PAPER);watch.text(xx+10,yy+18,'PULL',10,True,NAVY);watch.line(xx+20,yy+8,xx+20,yy+14,NAVY,.5);watch.line(xx+20,yy+14,xx+18,yy+12,NAVY,.5);watch.line(xx+20,yy+14,xx+22,yy+12,NAVY,.5)
 elif title=='PRZEWÓD':watch.text(xx+4,yy+8,'FORMA / S1',8,True,PAPER);watch.text(xx+4,yy+3,'CABLE LABEL / DEMO',4.3,False,PAPER)
 elif title=='ETYKIETA S1':watch.text(xx+4,yy+8,'S1 / MODEL DEMONSTRACYJNY',5.9,True);watch.text(xx+4,yy+3,'ID: 0001 / WŁASNY PROJEKT',4.6)
 elif title=='FORMA':watch.text(xx+4,yy+16,'CZAS PO',10,True,PAPER);watch.text(xx+4,yy+8,'TWOJEJ STRONIE.',8,True,PAPER)
 else:logo(watch,xx+6,yy+16,10,NAVY);watch.text(xx+4,yy+6,'S1 / CONCEPT EDITION',5.3,True,NAVY)
 watch.op(True);watch.outline(xx,yy,ww,hh,CUT,.15);watch.op(False)
watch.text(12,65,'WŁASNE ŹRÓDŁA WEKTOROWE / ROZMIARY W mm',6,True);watch.para(12,56,'Warstwa cięcia jest osobnym kolorem dodatkowym. Na ekranie to przykładowa etykieta folii ochronnej, bez udawania materiału producenta.',125,7);watch.end()

# Original front/side/back product drawings with actual placement regions.
watch.begin(148,210,3);watch.rect(0,0,154,216,PAPER);watch.text(10,200,'S1 / ROZMIESZCZENIE BRANDINGU',12,True)
for xx,title in [(15,'PRZÓD'),(68,'TYŁ')]:
 watch.rect(xx+8,101,24,72,CREAM);watch.rect(xx,119,40,46,NAVY);watch.text(xx+6,176,title,7,True)
 watch.text(xx+12,168,'FORMA',4.7,True,NAVY);watch.outline(xx+10,103,20,6,NAVY,.3);watch.line(xx+20,103,xx+20,109,NAVY,.3);watch.text(xx+12,104.5,'F',3.5,True,NAVY)
 if title=='PRZÓD':
  watch.rect(xx+3,122,34,40,PAPER);watch.text(xx+8,143,'09:41',12,True,NAVY);watch.text(xx+9,131,'FORMA',6,True,NAVY)
 else:watch.circle(xx+20,142,12,CREAM);watch.text(xx+12,141,'S1',11,True);watch.text(xx+8,124,'CONCEPT / DEMO',4.7)
watch.rect(124,119,10,46,NAVY);watch.rect(134,145,2,7,CREAM);watch.text(118,176,'BOK',7,True);watch.text(115,111,'POWER',5.2)
watch.circle(135,148.5,.55,NAVY);watch.line(128,116,135,143,NAVY,.15)
watch.line(15,93,55,93,NAVY,.18);watch.text(27,87,'40 mm',7,True);watch.line(61,119,61,165,NAVY,.18);watch.text(60,112,'46 mm',6)
watch.para(12,68,'Oznaczenia demonstracyjne: ekran, przycisk, pasek, sprzączka i plecki. Rysunki mają własną geometrię i służą do oceny przygotowania kompletu DTP.',128,8)
watch.text(12,18,'RYSUNKI WEKTOROWE / AUTORSKI MODEL KONCEPCYJNY',6.5,True);watch.text(12,11,'To nie jest specyfikacja wyprodukowanego urządzenia.',6);watch.end();watch.save()
(OUT/'source-data.json').write_text(json.dumps({'status':'OWN_TECHNICAL_DEMOS_NOT_COMMERCIAL_CASES','labels':{'count':5,'trim_mm':[155,60],'bleed_mm':3,'white_choke_mm':.15,'white_clear_window_mm':[7,6,10,5],'texts_are_outlines':True,'EAN':ean},'watch':{'production_pdf_pages':len(watch.pages),'box_nominal_mm':[45,70,20],'glue_tab_mm':12,'insert_mm':[43,67],'manual_pages':4,'all_parts':'Main box, insert, four-page manual, screen/cable/product/sticker labels and front/side/back branding drawings','not_claimed':'Not a printed customer case, certified physical die, tested smartwatch, Pantone swatch match or compliance approval.'},'font_use':'System Arial outlines; no font files distributed.','production_profile':'DeviceCMYK plus named spots. No PDF/X certification or printer-specific ICC assumed.','printer_inputs':'Client supplies approved dieline, exact texts, ink definitions, profile and PDF standard before final production.'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('AUTHORED',len(labels.pages),'label pages and',len(watch.pages),'watch pages')
