WARSTWOWY MODEL 3D — WŁASNA PRÓBKA WARSZTATU

Plik: layered-roof-own-sample.blend
Utworzono i sprawdzono natywnym silnikiem Blender 5.2.2 LTS.

To autorska, poglądowa scena przygotowana do pokazania sposobu organizacji
modelu. Nie przedstawia wykonanej realizacji klienta ani zatwierdzonego
rozwiązania budowlanego. Wymiary i układ warstw są demonstracyjne.
Nie zawiera referencji klienta ani cudzych tekstur lub modeli.

CO JEST W ŚRODKU
8 osobnych kolekcji i 73 rzeczywiste obiekty typu mesh:
01 — płyta spodnia
02 — siatka z osobnych prętów
03 — bloki izolacji
04 — poszycie i membrana
05 — kontrłaty
06 — łaty
07 — profilowane pokrycie
08 — deska okapowa, rynna i rura

Materiały mają proceduralne powierzchnie drewna i warstw mineralnych.
Nie wymagają pobierania tekstur. Pokrycie ma prawdziwy profil geometryczny;
rynna i rura mają grubość ścianek. Obiekty i materiały można edytować.

JAK SPRAWDZIĆ
1. Otwórz plik .blend w Blenderze 5.2 lub nowszym.
2. W Outlinerze wyłącz widoczność kolekcji 05, 06, 07 i 08.
3. Pozostałe warstwy zachowują kompletną geometrię.
4. Włącz warstwy ponownie. Każdą można ukryć niezależnie.

PODGLĄDY
01-assembled.png — złożony model z celowo skróconym pokryciem,
                  aby pokazać budowę próbki.
02-underlying-layers.png — te same obiekty po ukryciu górnych kolekcji.
03-exploded.png — widok rozstrzelony z tych samych brył.

WERYFIKACJA
native-verification.json zawiera wynik ponownego otwarcia pliku,
test ukrywania i przywracania wszystkich 8 kolekcji oraz test usunięcia
15 górnych obiektów, po którym zachowało się 58 obiektów spodnich.
To sprawdzenie edytowalności sceny, bez obliczeń konstrukcyjnych.

ODTWORZENIE
build_sample.py tworzy scenę i trzy rendery. Uruchom go w środowisku
Python 3.13 z oficjalnym modułem bpy==5.2.2 od Blender Foundation.
Może też posłużyć do dalszej parametryzacji sceny.
verify_native.py sprawdza zapisany plik natywnym silnikiem.

Właściwa realizacja wymaga osobnego uzgodnienia wymiarów, skali,
docelowych materiałów i wersji Blendera przed rozpoczęciem pracy.
