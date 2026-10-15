Własny fikcyjny protokół płatności, nie adapter realnego operatora. Python 3.13, tylko biblioteka standardowa.
Testy: python -m unittest discover -s . -p test_payment.py -v
Demo: python run_demo.py (wymaga nowej bazy results/fictional-demo.sqlite, nie nadpisuje poprzedniej).
HMAC SHA256 timestamp.rawJSON. Publiczny klucz ma nazwę demo-only-not-a-real-payment-key i NIE jest rzeczywistym sekretem.
Serwer wiąże wyłącznie127.0.0.1; nie wykonuje zewnętrznych płatności, maili ani wywołań realizacji.
Produkcja wymaga adaptera operatora, HTTPS, autoryzowanego API systemu zamówień, bezpiecznych sekretów oraz idempotentnego odbiorcy zewnętrznej kolejki. Cena2200NET dotyczy pełnego uzgodnionego1API/1operatora, nie tego mocka.
