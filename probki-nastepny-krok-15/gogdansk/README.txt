SOLID DIGITAL / WŁASNA DEMONSTRACJA TURYSTYCZNA

Fikcyjna marka: Szlak Motławy. Programy i ceny wyłącznie demonstracyjne.
Brak klienta, wyników kampanii, prawdziwych rezerwacji oraz płatności.
Wektory SVG, HTML, CSS i JS są źródłami tej własnej próbki.

Otwórz index.html lub uruchom lokalny serwer statyczny:
  python -m http.server 8765 --bind 127.0.0.1
Następnie http://127.0.0.1:8765/index.html

Testy rzeczywistego kodu (Python 3.10+, Node 18+; bez instalacji pakietów):
  python source.py
  node tests/tracker.test.cjs

Lokalny kontrakt request_booking rozwija własny framework ads-config.
Kontroluje zgodę, ścisły schemat, duplikaty, walutę, wartość 0 i dane osobowe.
Zdarzenie nie jest purchase. Brak jakiegokolwiek transportu do Google/Meta.
Historia jest przechowywana wyłącznie w pamięci karty i znika po odświeżeniu.
Idempotencja obejmuje wariant trasa/liczba osób w bieżącej karcie.
Brak potwierdzenia dostępności trasy i wysyłki wiadomości.

before.html: celowo przygotowany własny kontrprzykład SEO.
landing.html: faktyczne wdrożenie HTML po optymalizacji.
guide.html: pełny autorski poradnik (603 słowa wraz z nagłówkami).
seo-plan.json: 4 podstrony w proponowanym zakresie miesięcznym.
campaign-plan.json: 2 szkice Search i 2 Meta; nie eksport z platformy.
Przykład mediów 3000 PLN jest fikcyjny i osobny od 1600 PLN netto obsługi.
Wszystkie strony mają noindex,follow celowo dla demonstracji.
qa.json zawiera rzeczywisty wynik uruchomienia lokalnych testów.
Nie potwierdza zgodności aktualnych API, połączeń platform ani efektów SEO.
