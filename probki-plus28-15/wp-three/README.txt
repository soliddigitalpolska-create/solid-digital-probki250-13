TRZY ODRĘBNE WŁASNE WITRYNY WORDPRESS

PF: osobna witryna usługowa z pięcioma stronami i techniczną stroną potwierdzenia. Natywny formularz waliduje token, kontakt, zgodę i honeypot; poprawne zgłoszenie zapisuje w prywatnym typie wpisu oraz pokazuje w panelu. Nie wysyła e-maili.

Cypr / notes: osobna witryna katalogowa, z własną stroną główną, filtrem WP_Query, dwiema fikcyjnymi ofertami, mediami i polami SEO. To samodzielny katalog; nie jest wcześniejszą pojedynczą ofertą Cypr dodaną do odziedziczonego sklepu.

Pracownia / WooCommerce: odizolowana kopia własnego rzeczywistego warsztatu. Dwa świeże checkouty BACS utworzyły natywne zamówienia produktu fizycznego i usługi. Nie pobrano pieniędzy ani nie wysłano e-maili. Ewidencja i rezerwacja zapasu są wyłączone w tym przykładzie SQLite.

Wszystkie marki, dane i produkty są fikcyjne. To nie są płatne realizacje ani trzej klienci. Publiczne HTML to statyczne portfolio i prawdziwe zrzuty. Serwery WordPress działają lokalnie w odrębnych sandboxach; ich adresy w dowodach JSON opisują środowisko testu, nie działające publicznie zaplecze.

EDYCJA I ŹRÓDŁA
Interfejs codziennej edycji to natywny Classic / TinyMCE. Nie deklarujemy działającego wizualnego canvasu Gutenberga w użytej przeglądarce. Treści i szablony zachowują natywny zapis bloków WordPress.

Pakiet zawiera autorskie motywy, pluginy workflow, importery i odczyty PHP, wybrane eksporty publicznej treści CMS oraz własne media. WordPress core, zewnętrzne pluginy, bazy, konfiguracje, konta, cookies i pliki prywatnych serwerów nie są publikowane. Lokalny pomocnik logowania administratora również jest wyłączony z pakietu.

Importery są demonstracjami do odizolowanych instalacji WordPress. Tryb create zastępuje startową treść własnym fikcyjnym scenariuszem; nie uruchamiać go w produkcji lub u klienta. Publiczne źródła nie są automatyczną migracją pełnego serwera. Odtworzenie wymaga istniejącego WordPressa, PHP i prawidłowej bazy. Ścieżki importerów należy dostosować do własnego układu katalogów. Folder seed-data zawiera wyłącznie nasze fikcyjne dane i grafiki.

POMIARY
Sześć pełnych raportów JSON i HTML z oficjalnego Lighthouse 13.5.0 oraz Google Chrome, z lokalnych serwerów. Finalne testy używają oficjalnego API pakietu NPM z jawnym zamknięciem własnego headless Chrome. Pierwszy CLI wygenerował poprawny raport, ale proces Windows nie zakończył sprzątania; ten stan jest zapisany w dowodach roboczych.

Wyniki są syntetyczne i lokalne, nie są raportem Google PSI z produkcji ani pomiarem terenowym. Celowe noindex demonstracji obniża ocenę SEO. Nie ukrywamy słabszego wyniku sklepu na mobile i nie gwarantujemy wyniku 90+ na nieznanym hostingu.

Moduł opinii Google w PF jest niepodłączony. Fikcyjna kancelaria nie ma prawdziwego profilu ani recenzji. Właściciel przyszłej witryny musi dostarczyć uprawniony profil lub kod widżetu; nie deklarujemy sprawdzonego odczytu Google API.
