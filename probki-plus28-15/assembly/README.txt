WOOD 01 — autorska próbka animowanej instrukcji montażu

wood01-montaz.blend: samodzielna scena Blender 5.2.2, 912 klatek, 24 fps, rzeczywiste kluczowanie sześciu paneli i 32 obiektów łączników. Kamera nieruchoma.
wood01-geometry.blend: własny model bazowy 800 × 350 × 600 mm.
wood01-instrukcja-montazu.mp4: 38 sekund, Full HD, H.264.
Wektorowe napisy, etykiety i schemat łącznika pochodzą z encode.py; geometria, krawędzie i ruch są renderowane w Blenderze. Brak zewnętrznej muzyki i lektora.

Skrypty stanowią zapis warsztatu w lokalnym workspace; katalog ROOT w skryptach oraz ścieżkę do modułu bpy i FFmpeg należy dostosować przy odtwarzaniu w innym środowisku. Sam plik .blend nie wymaga tych skryptów do otwarcia i edycji animacji.
Przy niezależnym rebuildzie build_motion.py parametr SOURCE powinien wskazać dołączony wood01-geometry.blend.

To jeden własny projekt demonstracyjny. Pakiet nie zawiera materiału referencyjnego klienta ani realizacji komercyjnej.
