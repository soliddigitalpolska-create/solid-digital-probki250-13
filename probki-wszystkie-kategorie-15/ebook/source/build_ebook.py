from pathlib import Path
import json,hashlib,html,re
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from pypdf import PdfReader
P=Path(__file__).resolve().parent/'ebook-proof';P.mkdir(exist_ok=True)
PUB=P/'public';PUB.mkdir(exist_ok=True)
for n,f in [('Regular','calibri.ttf'),('Bold','calibrib.ttf'),('Light','calibril.ttf')]:pdfmetrics.registerFont(TTFont(n,str(Path('C:/Windows/Fonts')/f)))
W,H=419.53,595.28;NAVY='#163139';CREAM='#F4F1E9';ORANGE='#E9774B';MUTED='#627373';SAGE='#DDE8DF'
style=ParagraphStyle('body',fontName='Regular',fontSize=11,leading=15.6,textColor=HexColor(NAVY),spaceAfter=10)
styleb=ParagraphStyle('big',parent=style,fontName='Bold',fontSize=15,leading=20)
pages=[
('01','Zanim otworzysz kalendarz','Wybierz rezultat, nie liczbę zadań.',[
 'Długi plan może dawać poczucie porządku, a mimo to nie wskazywać, co powinno być gotowe w piątek. Zacznij od prostszego pytania: co ma zmienić się dzięki temu tygodniowi?',
 'Ten mini-e-book proponuje autorski sposób organizacji pracy: zrzut zadań, trzy rezultaty, bloki czasu, codzienne zamknięcie i krótki przegląd. To propozycja do samodzielnego dopasowania, bez obietnicy określonej wydajności.',
 '<b>Przykład.</b> Zamiast „pracować nad stroną” zapisz: „przekazać gotowe pięć podstron do jednej zbiorczej rundy uwag”. Taki zapis ma widoczny koniec.',
 '<b>Na dziś:</b> wybierz jedną zaległą sprawę. Napisz, jaki plik, decyzja lub efekt zakończy jej obecny etap. Nie dodawaj jeszcze terminu.'
 ]),
('02','Zrób zrzut zadań','Jedno miejsce na wszystkie otwarte sprawy.',[
 'Przejrzyj notatki, skrzynkę i ostatnie rozmowy. Przenieś zadania na jedną listę. Na tym etapie zapisuj je krótko: bez układania całego tygodnia i bez dopracowywania narzędzia.',
 'Przy każdym punkcie dodaj źródło oraz najbliższy krok. „Poprawić ofertę” może oznaczać trzy różne rzeczy; „sprawdzić uwagi z wiadomości klienta i zmienić zakres w dokumencie” jest już działaniem.',
 '<b>Podziel listę:</b><br/>DO ZROBIENIA - mogę wykonać następny krok.<br/>OCZEKUJE - potrzebuję danych lub decyzji innej osoby.<br/>PÓŹNIEJ - sprawa nie należy do tego tygodnia.',
 'W fikcyjnym projekcie strony „dodać galerię” trafia do OCZEKUJE, jeżeli brakuje zdjęć. Następny krok to poprosić o konkretne pliki, a nie rezerwować godzinę na ich wstawianie.',
 '<b>Na dziś:</b> usuń z listy przynajmniej jeden niejasny zapis i zamień go w działanie albo pytanie.'
 ]),
('03','Trzy rezultaty tygodnia','Wskaż małą liczbę spraw, które doprowadzisz do końca.',[
 'Przeczytaj listę i wybierz trzy rezultaty. Liczba trzy jest roboczym ograniczeniem tego modelu, a nie uniwersalną normą. Jeśli masz mało czasu lub jedno duże zobowiązanie, wybierz mniej.',
 'Każdy rezultat opisz jako rzecz do sprawdzenia: gotowy dokument, zamknięta lista poprawek, zaakceptowany układ lub porównanie wariantów z rekomendacją.',
 '<b>Przykładowy tydzień projektanta:</b><br/>1. Przekazać pięć ekranów do zbiorczej oceny.<br/>2. Uporządkować zdjęcia i opisy dziesięciu produktów.<br/>3. Zamknąć archiwum poprzedniego projektu.',
 'Nie wpisuj „uzyskać akceptację” jako pewnego rezultatu, jeśli decyzja należy do klienta. Zapisz własną część: „przekazać kompletną paczkę i termin na odpowiedź”.',
 '<b>Na dziś:</b> sprawdź, czy wszystkie trzy rezultaty zależą przede wszystkim od działań, które możesz rzeczywiście wykonać.'
 ]),
('04','Zarezerwuj bloki','Kalendarz ma pokazywać także granice.',[
 'Najpierw wpisz stałe obowiązki. Dopiero pozostały czas podziel na bloki, w których można wykonać następny krok jednego rezultatu. Nie zakładaj, że każda wolna minuta jest godziną głębokiej pracy.',
 'W przykładowym dwugodzinnym oknie można przeznaczyć 70 minut na wybrany rezultat, 30 na sprawy bieżące i 20 na kontrolę oraz zamknięcie. To punkt startowy do sprawdzenia w swoim rytmie, nie sztywna reguła.',
 '<b>Poniedziałek:</b> ustalenie kierunku i pierwszy ekran.<br/><b>Wtorek:</b> dwa kolejne ekrany.<br/><b>Środa:</b> pozostałe widoki.<br/><b>Czwartek:</b> kontrola kompletności i eksport.<br/><b>Piątek:</b> przekazanie paczki i przegląd.',
 'Blok nazwij rezultatem. „Projekt” nie mówi, co otworzyć po rozpoczęciu pracy. „Dokończyć układ oferty i sprawdzić wersję mobilną” daje konkretny początek.',
 '<b>Na dziś:</b> zarezerwuj jeden blok i zapisz, co ma istnieć po jego zakończeniu.'
 ]),
('05','Zapisz następny krok','Zmniejsz zadanie do działania, które da się rozpocząć.',[
 'Kiedy zadanie stoi, sprawdź, czy opisuje pojedyncze działanie. „Zrobić marketing” jest obszarem odpowiedzialności. „Wybrać trzy zdjęcia do posta o nowej usłudze” można rozpocząć od razu.',
 '<b>Zamiast:</b> przygotować prezentację.<br/><b>Zapisz:</b> wypisać pięć pytań odbiorcy i przypisać do nich po jednym slajdzie.',
 '<b>Zamiast:</b> poprawić dane.<br/><b>Zapisz:</b> porównać dziesięć pierwszych wierszy z plikiem źródłowym i oznaczyć różnice.',
 '<b>Zamiast:</b> skończyć projekt.<br/><b>Zapisz:</b> otworzyć listę odbiorową i sprawdzić kolejno formularz, linki oraz widok telefonu.',
 'Dobry następny krok wskazuje czasownik, przedmiot i warunek zakończenia. Nie musi być drobny, ale powinien być jednoznaczny.',
 '<b>Na dziś:</b> przepisz trzy najstarsze zadania. Przy każdym wskaż plik lub narzędzie, od którego zaczniesz.'
 ]),
('06','Zostaw miejsce na zmianę','Bufor jest częścią planu.',[
 'Zadanie może potrwać dłużej, a brakujący materiał dotrzeć później. Plan zapełniony do ostatniej minuty nie pokazuje, jak przyjąć taką zmianę. Dlatego część dostępnego czasu pozostaw bez konkretnego zlecenia.',
 'Jeżeli pojawia się nowy pilny temat, sprawdź trzy rzeczy: jego rzeczywisty termin, wpływ na obecne zobowiązania i to, które zadanie ma ustąpić miejsca. Dopisanie go na górze listy nie tworzy dodatkowego czasu.',
 '<b>Przykładowa odpowiedź:</b><br/>„Mogę przygotować ten plik w czwartek. Wtedy paczkę zdjęć prześlę w piątek. Proszę o wybór priorytetu przed rozpoczęciem.”',
 'Własny błąd planowania zapisz jako obserwację. Zamiast „jestem za wolny” zanotuj „eksport i kontrola zajęły 40 minut, a w planie nie było na nie miejsca”. To wskazówka do kolejnego tygodnia.',
 '<b>Na dziś:</b> znajdź w kalendarzu miejsce na kontrolę gotowego materiału, a nie tylko jego wykonanie.'
 ]),
('07','Zamknij dzień','Pięć minut, które przygotowuje kolejny początek.',[
 'Zakończenie pracy nie musi oznaczać zakończenia wszystkich spraw. W tym modelu oznacza zapisanie stanu, tak aby jutro nie odtwarzać go z pamięci.',
 '<b>1. Zapisz wykonany rezultat.</b> Nazwij plik, decyzję lub etap, który jest gotowy.',
 '<b>2. Zapisz jedną blokadę.</b> Jeśli czekasz na materiał, wskaż dokładnie na jaki i od kogo.',
 '<b>3. Wybierz początek jutra.</b> Zostaw jeden następny krok oraz link do właściwego pliku.',
 '<b>4. Sprawdź kalendarz.</b> Upewnij się, że kolejny blok nadal jest realny.',
 '<b>5. Zamknij listę.</b> Pozostałe pomysły odłóż do wspólnej skrzynki zadań.',
 'Przykład zapisu: „Gotowe: układ pięciu ekranów. Czekam: opis usługi B. Jutro: porównać ekran kontaktu z listą wymagań i sprawdzić formularz”.'
 ]),
('08','Przejrzyj tydzień','Patrz na fakty, które pomogą zaplanować następny.',[
 'W piątek wróć do trzech rezultatów. Przy każdym zapisz: gotowe, przekazane, oczekuje lub przeniesione. Sam status ma niewiele wartości bez krótkiego powodu.',
 '<b>Co zostało ukończone?</b><br/>Paczka pięciu ekranów została przekazana. Wszystkie pliki mają spójne nazwy i link do podglądu.',
 '<b>Co czeka?</b><br/>Opisy produktów wymagają potwierdzenia dwóch parametrów. Pytanie wysłano z konkretną listą braków.',
 '<b>Co zmienisz?</b><br/>Kontrolę eksportu zaplanuj wcześniej. Nie rezerwuj czasu na zadanie bez materiałów.',
 'Przenieś tylko zadania nadal potrzebne. Nie kopiuj automatycznie całej starej listy. Sprawdź, czy zmienił się termin, zakres lub osoba odpowiedzialna.',
 '<b>Na dziś:</b> zapisz jedną rzecz do zachowania i jedną do zmiany. Do następnego planu wpisz te wnioski, a nie ocenę własnego charakteru.'
 ]),
('09','Zobacz pełny przykład','Fikcyjny tydzień małej pracowni.',[
 '<b>Założenie:</b> pięć popołudniowych okien po dwie godziny. Celem jest przekazanie projektu, uporządkowanie dziesięciu produktów i zamknięcie archiwum. Dane przykładu są fikcyjne.',
 '<b>Poniedziałek:</b> lista wymagań, ustalenie układu, prośba o dwa brakujące opisy.',
 '<b>Wtorek:</b> dwa widoki projektu, porównanie parametrów pięciu produktów ze źródłem.',
 '<b>Środa:</b> pozostałe widoki, kolejne pięć produktów, oznaczenie niepotwierdzonych danych.',
 '<b>Czwartek:</b> kontrola telefonu i linków, eksport, przygotowanie paczki oraz krótkiej instrukcji.',
 '<b>Piątek:</b> przekazanie materiałów, lista pytań do odbiorcy, uporządkowanie archiwum i przegląd.',
 'Jeżeli odpowiedź klienta nie dotrze, blok nie znika. Można wykonać inną gotową część pracy, a materiały wymagające decyzji zostawić ze statusem OCZEKUJE. Zmiana planu pozostaje widoczna.'
 ]),
('10','Zacznij od jutra','Nie musisz przebudowywać całego systemu.',[
 'Wybierz jedno zadanie, które od kilku dni wraca na listę. Zapisz jego źródło, widoczny rezultat i najbliższy krok. Następnie zarezerwuj jeden realny blok na wykonanie.',
 '<b>Przed rozpoczęciem:</b> sprawdź, czy masz potrzebne dane i uprawnienia. Jeśli czegoś brakuje, nazwij brak i poproś o konkretny materiał.',
 '<b>W trakcie:</b> pracuj nad wybranym krokiem. Nowe pomysły zapisuj w skrzynce zadań, bez natychmiastowej zmiany celu bloku.',
 '<b>Po zakończeniu:</b> obejrzyj wynik, zapisz status i zostaw początek kolejnego kroku. Jeśli czas był niedoszacowany, zanotuj rzeczywistą długość wraz z kontrolą.',
 'Po tygodniu zachowaj elementy, które rzeczywiście ułatwiły pracę. Pozostałe uprość lub usuń. Ten materiał ma służyć działaniu; możesz zmienić liczbę rezultatów, długość bloków i formę notatek.',
 '<b>Własny materiał demonstracyjny CloudCode Studio.</b> Tekst i projekt powstały na fikcyjnym przykładzie. To kompletna mini-publikacja pokazująca redakcję i skład, bez obietnic określonych efektów lub sprzedaży.'
 ])]
pdf=PUB/'tydzien-bez-chaosu-demo.pdf';c=canvas.Canvas(str(pdf),pagesize=(W,H));c.setTitle('Tydzień bez chaosu - autorski mini-e-book demonstracyjny');c.setAuthor('CloudCode Studio')
layout=[]
def para(text,y,s=style,x=40,width=W-80):
 p=Paragraph(text,s);_,h=p.wrap(width,y-45);p.drawOn(c,x,y-h);return y-h-12
def footer(no):
 c.setStrokeColor(HexColor('#C8D2CA'));c.line(40,38,W-40,38);c.setFillColor(HexColor(MUTED));c.setFont('Regular',8);c.drawString(40,24,'TYDZIEŃ BEZ CHAOSU / WŁASNA PRÓBKA');c.drawRightString(W-40,24,f'{no:02d} / 11')
# Cover: vector typography with original grid motif.
c.setFillColor(HexColor(CREAM));c.rect(0,0,W,H,fill=1,stroke=0)
c.setFillColor(HexColor(NAVY));c.rect(0,H-18,W,18,fill=1,stroke=0);c.setFont('Bold',10);c.drawString(40,H-64,'CLOUDCODE / PRACOWNIA')
c.setFont('Light',43);c.drawString(40,H-150,'Tydzień');c.drawString(40,H-200,'bez chaosu.')
c.setFont('Regular',14);c.drawString(42,H-239,'Mały system. Widoczny rezultat.')
c.setFillColor(HexColor(SAGE));c.roundRect(40,122,W-80,170,12,fill=1,stroke=0)
for i in range(5):
 x=57+i*61;c.setFillColor(HexColor('#C5D7C9'));c.roundRect(x,148,45,112,7,fill=1,stroke=0)
 c.setFillColor(HexColor(NAVY));c.setFont('Bold',10);c.drawCentredString(x+22.5,236,['PON','WT','ŚR','CZW','PT'][i]);c.setFillColor(HexColor(ORANGE if i==3 else NAVY));c.roundRect(x+7,163+(i%3)*11,31,34+(i%2)*18,4,fill=1,stroke=0)
c.setFillColor(HexColor(MUTED));c.setFont('Regular',10);c.drawString(40,78,'11 stron / konkretny przykład / własny projekt')
footer(1);c.showPage()
for n,(num,title,lead,body) in enumerate(pages,2):
 c.setFillColor(HexColor(CREAM));c.rect(0,0,W,H,fill=1,stroke=0);c.setFillColor(HexColor(ORANGE));c.setFont('Bold',11);c.drawString(40,H-49,'ROZDZIAŁ '+num)
 y=H-74;y=para(title,y,ParagraphStyle('title',parent=style,fontName='Bold',fontSize=27,leading=30));y=para(lead,y,styleb)
 c.setStrokeColor(HexColor('#CAD6CD'));c.line(40,y+2,W-40,y+2);y-=14
 for text in body:y=para(text,y)
 assert y>47,(n,title,y)
 layout.append({'page':n,'title':title,'last_text_y':round(y,2),'no_bottom_overflow':True});footer(n);c.showPage()
c.save();reader=PdfReader(pdf);assert len(reader.pages)==11
for n,page in enumerate(reader.pages):assert len(page.extract_text())>100
# Standalone sales-page: deliberately a demo, with a native local product destination.
sales='''<!doctype html><html lang="pl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tydzień bez chaosu / własny e-book</title><style>*{box-sizing:border-box}body{margin:0;background:#f4f1e9;color:#163139;font:17px/1.65 Arial}main{max-width:1080px;margin:auto;padding:44px 28px}header{border-bottom:1px solid #c8d2ca;display:flex;justify-content:space-between;font-size:12px;font-weight:bold;letter-spacing:1px;padding-bottom:20px}.hero{display:grid;grid-template-columns:1.15fr .85fr;gap:60px;align-items:center;padding:70px 0}h1{font-size:clamp(43px,6vw,72px);line-height:1.04;letter-spacing:-3px;margin:20px 0}h2{font-size:30px;line-height:1.2}small{font-size:12px;color:#627373}.eyebrow{color:#bc4b24;font-size:12px;font-weight:bold;letter-spacing:2px}.cover{width:100%;max-width:330px;box-shadow:0 25px 50px #16313925;transform:rotate(3deg)}a.btn{display:inline-block;background:#163139;color:white;padding:14px 22px;border-radius:7px;text-decoration:none;margin:12px 10px 12px 0}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.card{background:#e0e9df;padding:24px;border-radius:12px}.note{padding:24px;border-left:4px solid #e9774b;background:#fffaf1;margin-top:40px}section{padding:30px 0}footer{font-size:12px;color:#627373;border-top:1px solid #c8d2ca;padding:22px 0}@media(max-width:720px){.hero,.cards{grid-template-columns:1fr;gap:28px}.hero{padding:34px 0}.cover{transform:none;max-width:250px}.hero figure{margin:auto}h1{letter-spacing:-1.5px}}</style><main><header><span>CLOUDCODE / WŁASNA PUBLIKACJA</span><span>DEMO / 2026</span></header><div class="hero"><div><p class="eyebrow">MINI-E-BOOK / PDF</p><h1>Tydzień<br>bez chaosu.</h1><p>Przenieś otwarte sprawy do jednego miejsca. Wybierz trzy rezultaty, zarezerwuj realny czas i zostaw sobie jasny początek jutra.</p><p><b>11 stron. Konkretny przykład. Prosty system do dopasowania.</b></p><a class="btn" href="tydzien-bez-chaosu-demo.pdf">Pobierz całą własną próbkę PDF</a><p><small>Bezpłatny podgląd demonstracyjny. Ten przycisk nie pobiera opłaty.</small></p></div><figure><img class="cover" src="cover.png" alt="Autorska typograficzna okładka Tydzień bez chaosu"></figure></div><section><h2>Co znajdziesz w środku</h2><div class="cards"><div class="card"><b>Jedna lista</b><p>Zadania do wykonania, sprawy oczekujące i tematy na później.</p></div><div class="card"><b>Widoczny rezultat</b><p>Trzy priorytety i następny krok, który można rozpocząć.</p></div><div class="card"><b>Realny tydzień</b><p>Bloki, miejsce na zmianę oraz przegląd fikcyjnego projektu.</p></div></div></section><section><h2>Dla kogo jest ten materiał</h2><p>Dla osoby prowadzącej kilka małych projektów, która chce wypróbować prosty sposób planowania. To autorska propozycja organizacji pracy; możesz zmienić liczbę priorytetów i długość bloków.</p></section><section><h2>Jak wygląda kompletne wdrożenie sprzedaży</h2><p>Projekt może obejmować taki PDF i okładkę, stronę oferty, produkt cyfrowy WooCommerce, płatność na koncie właściciela oraz automatyczne nadanie prawa do pobrania po potwierdzonym zamówieniu.</p><p>Ta strona pokazuje własny warsztat redakcji i składu. Osobny lokalny test sprawdza natywny stan zamówienia i uprawnienie WooCommerce. Nie uruchomiono publicznego zakupu, BLIK ani wysyłki e-mail.</p></section><div class="note"><b>Charakter próbki</b><p>Wszystkie teksty, układ i ilustracja okładki są własne. Przykłady są fikcyjne. To demonstracja przygotowana do oceny warsztatu, bez historii płatnego klienta i bez obietnic zysków.</p></div><footer>Własna publikacja demonstracyjna CloudCode Studio. PDF: 11 stron, plik do pobrania. Brak formularza i zewnętrznego trackingu.</footer></main></html>'''
(PUB/'index.html').write_text(sales,encoding='utf-8')
(PUB/'ebook-content.json').write_text(json.dumps({'title':'Tydzień bez chaosu','original_own_demo':True,'pages':pages},ensure_ascii=False,indent=2),encoding='utf-8')
(P/'pdf-validation.json').write_text(json.dumps({'pages':11,'bytes':pdf.stat().st_size,'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'text_extraction_all_pages':True,'layout':layout,'visual_review':'PENDING_RENDER'},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pdf':str(pdf),'pages':11,'bytes':pdf.stat().st_size,'body_words':sum(len(re.sub('<[^>]+>','',b).split()) for _,_,_,bs in pages for b in bs)},ensure_ascii=False))
