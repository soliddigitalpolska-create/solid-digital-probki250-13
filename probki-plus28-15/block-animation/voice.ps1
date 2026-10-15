Add-Type -AssemblyName System.Speech
$taskNarrator = New-Object System.Speech.Synthesis.SpeechSynthesizer
$taskNarrator.SelectVoice('Microsoft Paulina Desktop')
$taskNarrator.Rate = 1
$taskVoiceDir = Join-Path $PSScriptRoot 'audio'
New-Item -ItemType Directory -Force -Path $taskVoiceDir | Out-Null
$taskPhrases = @(
 'Spójrz na całość.',
 'Teraz przyjrzyj się szczegółowi.',
 'Zamieńmy kolejność.',
 'Właśnie tak. Ruch podąża za słowem.'
)
for ($taskPhraseIndex = 0; $taskPhraseIndex -lt $taskPhrases.Count; $taskPhraseIndex++) {
 $taskNarrator.SetOutputToWaveFile((Join-Path $taskVoiceDir ('vo-{0:d2}.wav' -f ($taskPhraseIndex + 1))))
 $taskNarrator.Speak($taskPhrases[$taskPhraseIndex])
}
$taskNarrator.Dispose()
$taskPhrases | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'voice-text.json') -Encoding UTF8
