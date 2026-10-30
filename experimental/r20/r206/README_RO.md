# R2.0.6 — Selective ASR Recovery Lab (experimental, read-only)

## Scop
Recuperarea sincronurilor incerte din modulul 01 fără revenire la timecode-ul reporterului și fără reducerea pragurilor de încredere. Acest director conține instrumente **candidate**, nu un release instalabil și nu cod executat automat în Premiere.

Motorul primește numai diagnosticul local de tip `aive-match-diagnostic-v1` și generează un JSON **de cereri de retranscriere** `aive-r206-asr-rescan-request-v1`. Nu generează tăieturi IN/OUT, nu schimbă proiectul, nu acceptă automat potrivirile. Dacă intervalele nu pot fi stabilite în siguranță, produce BLOCKED + necesitate de revizuire.

## Politici tehnice
- `REVIEW_NO_MATCH`, `REVIEW_WEAK_TRANSCRIPT`, `REVIEW_ALTERNATIVE_OCCURRENCE`: întreaga sursă dacă durata este <= 8 min, altfel BLOCKED + reper editorial. 
- `REVIEW_WEAK_BOUNDARY`: fereastră în jurul limitelor ASR candidate (+/-20s); TC reporter poate ghida doar zona de **căutare** când nu există ancoră ASR sigură.
- Lipsă completă de TC cu sursă <=8 min: căutare pe întreaga sursă, nu TC inventat; peste 8 min: BLOCKED.
- Mai multe cereri suprapuse din aceeași sursă se unesc, cu lista CUT-urilor afectate și motive.
- Cod sursă ASR contradictoriu, durate contradictorii, CUT duplicat, statut necunoscut => STOP sau BLOCKED.
- Pentru fiecare rezultat sunt permanent `automaticCuttingAllowed:false` și `safeToModifyPremiereTimeline:false`.
- Nu exporta `scriptText`, `startHeard`, `endHeard`, speaker, DOCX path, transcrieri sau fișiere media. Planul trebuie păstrat LOCAL sub `D:\AI-Video-Editor\Temp\R206`, niciodată în GitHub public.
- Nu modifica `R1.9.13` sau algoritmul existent. Execuția nouă trebuie integrată numai după evaluarea ASR multilingual, teste GPU reale și confirmarea pipeline-ului existent.

## CI
`.github/workflows/r206-selective-asr.yml` execută teste Python sintetice, fără audio, CUDA sau DOCX privat. Run confirmat: `40555364392`, PASS. Testele sunt incluse și în regresia automată read-only zilnică.

## Referință diagnostic real (doar statistică, fără date private)
19 CUT-uri din 7 surse: 9 `REVIEW_SUGGESTED`, 7 `REVIEW_WEAK_BOUNDARY`, 1 `REVIEW_WEAK_TRANSCRIPT`, 2 `REVIEW_NO_MATCH`. Rezultatul planului de retranscriere și viitoarea potrivire sunt **candidate pentru evaluare**, nu aprobări editoriale.

## ACCEPTARE rămasă
Integrarea în modul 01 cu notificare de progres și cache valid, retranscriere audio reală numai pentru ferestrele selectate, comparație cu DOCX, tratarea halucinațiilor ASR pe surse ambianță, teste LIVE în Premiere, zero fallback TC, audit JSON local și rollback. Până atunci 01 rămâne fail-closed pe incertitudini.


## Implementare ulterioară în aceeași ramură — executor ASR local, încă neintegrat în 01
- `tools/r206_retranscribe.py` este un **executor real opt-in**, nu doar un calculator de ferestre: decupează în mod local fiecare interval prin FFmpeg într-un WAV temporar mono 16 kHz, cere durata prin ffprobe și folosește modelul CTranslate2 local preinstalat `faster_whisper.WhisperModel`. Nu descarcă automat modele și nu contactează servicii externe.
- Decodarea cu `beam_size=5`, `temperature=0`, `condition_on_previous_text=False`, `word_timestamps=True`, `vad_filter=False`, `task=transcribe` este o **configurație candidat**, NU un benchmark/calibrare pe RTX3070. Limba se detectează automat, dar vorbirea mixtă ro-ru necesită verificare.
- Fișierele WAV temporare sunt eliminate automat, fiecare cuvânt are timestamp absolut față de sursă, iar rezultatul este întotdeauna `REVIEW_REQUIRED` cu `automaticCuttingAllowed:false`. Lipsa cuvintelor și repetițiile apar ca alerte, fără a fi acceptate orbește.
- Verifică preflight pentru media offline, extensii, fereastră în afara duratei, coduri duplicate și sursă schimbată (durata ffprobe vs diagnostic); orice eroare blochează procesarea, fără modificări în Premiere. Rezultatele ASR conțin transcript privat și se păstrează NUMAI local, niciodată în repository.
- Parametrul explicit `--execute` și modelul local previn rularea întâmplătoare. Integrarea finală va fi invocată prin butonul existent 01, fără comenzi manuale cerute utilizatorului.
- **CI MOCK PASS:** https://github.com/Sankio9/ai-video-editor-updates/actions/runs/40556352429 — 18 teste planner + 12 teste executor/FFmpeg/CUDA simulate (30 total), cu Python compile. Niciun test nu a utilizat fișiere reale media, RTX3070, model ASR sau Premiere LIVE. Nu afirma performanța/precizia audio.
