# Veyrelo — narzędzia w przeglądarce

Trzy statyczne narzędzia: brief projektowy, analiza CSV i kalkulator nakładu pracy. Dane wejściowe są przetwarzane lokalnie. Brak API, zapisu do serwera i analityki. Eksport i ponowne otwarcie plików są ręczne.

Uruchomienie testów: Node.js 22+; z tego katalogu `npm test`. Brak zależności npm. Strony są publikowane przez GitHub Pages.

CSV: wybrane reguły kontroli danych; to nie jest certyfikacja ani pełna walidacja Merchant Center. Cyfra kontrolna GTIN nie potwierdza przydzielenia numeru. Eksport nie uzupełnia danych produktowych.

Kalkulator: wartość uwolnionego czasu nie jest wpływem gotówki ani gwarancją oszczędności. Wyniki zależą od podanych założeń.

## 25 funkcji

- **B01** Scenariusze briefu: ceny, integracje i raporty
- **B02** Mierzalne kryteria odbioru
- **B03** Zależności i ograniczenia procesu
- **B04** Jawne wyłączenia zakresu
- **B05** Lista materiałów do rozpoczęcia prac
- **B06** Budżet i termin jako opcjonalne ograniczenia
- **B07** Kontrola kompletności i braków briefu
- **B08** Eksport briefu do Markdown
- **B09** Eksport wersjonowanego JSON
- **B10** Lokalne wznowienie briefu z JSON
- **C01** Rozpoznawanie separatora CSV z ręcznym wyborem
- **C02** Obsługa cudzysłowów, wielu linii i BOM UTF-8
- **C03** Podgląd danych i profilowanie kolumn
- **C04** Mapowanie i kontrola wymaganych pól
- **C05** Wykrywanie powtórzonych identyfikatorów SKU
- **C06** Kontrola długości i sumy kontrolnej GTIN
- **C07** Walidacja cen i niejednoznacznych separatorów
- **C08** Kontrola składni adresów HTTP/HTTPS
- **C09** Podgląd bezpiecznych porządków i eksport CSV
- **C10** Raport błędów z numerami rekordów do JSON
- **K01** Obciążenie pracą w minutach, powtórzeniach i dniach
- **K02** Trzy scenariusze ograniczenia pracy
- **K03** Wartość uwolnionego czasu z kosztem utrzymania
- **K04** Próg pokrycia kosztu wdrożenia
- **K05** Eksport notatki decyzyjnej z założeniami

## Materiały odniesienia

- [GS1 US — cyfra kontrolna](https://www.help.gs1us.org/check-digit-calculator)
- [OWASP — ryzyko formuł w CSV](https://community.owasp.org/attacks/CSV_Injection)
