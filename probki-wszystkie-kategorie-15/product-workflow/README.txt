Własny lokalny workflow produktu, 2026-10-15. Python 3.13 + Pillow + FFmpeg.
Uruchom: python workflow.py --job inputs/job.json --output NOWY_KATALOG --preset product-focus --ratio 9:16 --size 1080 --ffmpeg PLIK_FFMPEG
Drugi preset: editorial. Druga orientacja: 16:9. Katalog wynikowy musi być nowy.
TTS w demo to lokalny systemowy głos, bez deklaracji komercyjnej licencji. Produkcyjne audio klienta/licencjonowany provider ustala się przed finansowaniem.
Bez LLM/API/video-gen w tym teście. Źródłem jest własny render Blender, nie fotografia klienta.
Testy: python -m unittest discover -s . -p test_workflow.py -v

Wideo wejściowe: użyj inputs/motion-job.json. Workflow zachowuje oryginalne klatki, zmienia proporcjonalnie rozmiar i może trzymać ostatnią klatkę, jeśli audio jest dłuższe. Źródło demo 540x960, eksport 1080p bez twierdzenia o dodanej jakości.
FFmpeg dla testów: ustaw zmienną FFMPEG_EXE na lokalny plik binarny albo dodaj ffmpeg do PATH.
