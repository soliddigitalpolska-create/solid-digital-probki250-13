TRZY WŁASNE WORKFLOW PYTHON/API

Autorskie demonstracje; dane i organizacje są fikcyjne. Biblioteka standardowa Python 3.13. Lokalne API testowe jest prawdziwym serwerem HTTP na loopback, nie zewnętrznym CRM. SQLite utrwala kontakty, przetworzone klucze, zamówienia, outbox, zgłoszenia, zadania, dead-letter i logi. Raporty i dokument HTML rzeczywiście powstały z danych wejściowych.

1. CSV -> API CRM: walidacja, kontrolowane HTTP429/503, maksymalnie3próby, backoff, idempotencja po ponownym otwarciu, dead-letter.
2. CSV zamówień -> kolejka -> jawna testowa akceptacja -> dokument HTML + outbox. Bez SMTP, e-maila, fakturowania i płatności. Kwoty liczone w całkowitych groszach. To nie jest faktura.
3. Webhook zgłoszeń -> reguły -> jawna testowa akceptacja/odrzucenie -> zadanie -> raport CSV. Nie użyto LLM. Formuła w danych CSV jest neutralizowana.

Odtworzenie w nowym katalogu:
python -m unittest discover -s sources -p test_workflows.py -v
python sources/run_demo.py --approve-demo --output local-demo-new

--approve-demo jawnie symuluje wejście recenzenta testowego. Nie deklaruje faktycznej oceny klienta ani automatycznej zgody modelu. Przed akceptacją zapis dokumentu/zadania jest blokowany. Bezpośrednie API też sprawdza status zatwierdzenia. API uruchamiane jest na losowym porcie127.0.0.1, zamykane po teście. Klient transportowy blokuje adresy spoza tego dokładnego lokalnego fixture, endpointy spoza listy i przekierowania. To ograniczenie kodu demonstracji, nie systemowy firewall.

Portfolio jest statycznym opisem istniejących wyników i logów; nie hostuje API. Bazy SQLite, prywatne briefy, ustawienia kont, hasła ani klucze nie są publikowane. Pełny kod i fikcyjne fixtures pozwalają odtworzyć lokalny przebieg. Nie prezentujemy płatnych wdrożeń ani doświadczenia w n8n/Make. Nie mierzyliśmy oszczędności czasu pracowników ani produkcyjnego SLA.
