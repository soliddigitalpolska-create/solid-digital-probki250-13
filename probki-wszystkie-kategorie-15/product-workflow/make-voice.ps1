param([Parameter(Mandatory=$true)][string]$OutputPath)
Add-Type -AssemblyName System.Speech
$speaker = [System.Speech.Synthesis.SpeechSynthesizer]::new()
$speaker.SelectVoice('Microsoft Paulina Desktop')
$speaker.Rate = 0
$speaker.SetOutputToWaveFile($OutputPath)
$speaker.Speak('Jedno źródło produktu. Dwa formaty publikacji. Ten sam kształt i detale. Wybierz układ, dodaj własny głos i napisy. Gotowy plik do akceptacji.')
$speaker.Dispose()
