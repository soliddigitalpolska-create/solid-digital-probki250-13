WŁASNA PRÓBKA CYPR EN→PL + NATYWNY WORDPRESS

Wszystkie dane i grafiki są fikcyjne. Brak materiałów klienta i płatnych realizacji.
index.html jest statycznym portfolio/eksportem, nie panelem CMS.
Rzeczywisty lokalny wpis WP28 istnieje w osobnym sandboxie; dowody w evidence/.
Pełny WordPress, baza, config i cookies nie są publikowane.

sources/native-post-export.json: eksport faktycznego wpisu, bloków i metadanych.
sources/native-gutenberg-content.html: rzeczywista serializacja bloków z bazy.
sources/own-cypr-classic-editor.php: portablemu-plugin, oficjalny corefilter use_block_editor_for_post tylko dla własnego postu i natywny metaboxSEO. Bez WordPresssalts/authcookies/credentials.
Interfejs edycji: natywny ClassicEditor/WYSIWYG z core. CanvasGutenberga był pusty w użytej przeglądarce; nie deklarujemy działającego wizualnego Gutenberga. Zapis12bloków w bazie zachowany.
sources/templates/single.html: faktycznie użyty natywny szablon z core/post-title/H1; nie zmienia12bloków treści wpisu.
evidence/native-template-h1-proof.json: dokładnie jeden H1 z tytułem wpisu i zgodny tytuł SEO.
sources/native-property.php: faktycznie wykonany własny importer PHP CLI; wymaga wcześniej przygotowanej odizolowanej instalacji WordPress w site/wordpress z aktywnym lokalnym SQLite i blokadą sieci/poczty. Uruchomienie create tworzy nowy wpis i dwa attachmenty; inspect czyta zapis. Nie uruchamiać w produkcji.
sources/plan.svg i dane.svg: oryginalne schematy wektorowe, nie fotografie.
sources/property-copy-demo-en-pl.txt: oryginalna karta źródłowa EN i opis PL.

evidence/create.json / inspect.json: oddzielne procesy PHP.
evidence/native-proof.json: SQL readonly, HTTP200, media200, edytor200 i restart.
evidence/original-integrity-before.json: hashe dwóch plików źródłowego warsztatu.

Grafika planu jest schematyczna. Nie jest rzutem technicznym i nie potwierdza proporcji nieruchomości. Wpis używa plików SVG dodanych przez kontrolowany importer; nie włączono dowolnego uploadu SVG dla użytkowników.
Nie deklarujemy panelu klienta, ACF Pro, płatnych wdrożeń, wyników sprzedaży ani pełnego procesu selekcji prawdziwych zdjęć dewelopera.
