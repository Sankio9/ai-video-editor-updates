# R2.0.4 — Cartoane V5 · checkpoint experimental

**2026-10-27 · LOCAL PASS · PREMIERE LIVE NOT TESTED · NOT PUBLISHED**

## Implementat
- Recuperat codul R2.0 real din pachet SOURCE-ONLY, fără reconstrucție.
- Mod 04 independent: modul aditiv r204_carton_layout.py și integrarea prin INTEGRATION_R204.patch.
- Rânduri compacte: minimum fezabil, maximum 4 × 33 caractere, fără reformularea textului.
- Accent semantic Orange/Bold: cifre, procente, unități, termeni relevanți, maximum două span-uri per pagină; indici Bold Words 1-based pe fiecare rând MOGRT.
- Pauze preferate la semne de punctuație, fără separarea inutilă a expresiilor evidențiate.
- Păstrare exactă a paginilor, textelor, separatorului de bloc, timingului EDITORIAL_PREVIEW.
- Niciun cod schimbat în 01/02/03/05; 05 rămâne HOLD. Fără QE și fără activare overwrite distructiv V5.

## Testare
- 7 teste generator R2.0 PASS.
- 11 teste unitare layout R2.0.4 PASS.
- 18 teste simulator ExtendScript MOGRT/collision/rollback PASS.
- 4 teste updater dual CEP root/SHA-256/rollback byte-exact PASS.
- Python compileall și sintaxă JSX PASS.
- Generator SHA-256 (local): c89e40ec345b51fb5a44f46fdad69b6d088371492e544da2ac1dbee385f8de0d
- Helper SHA-256 (local): caceca0f2d1f99729c7c18ae8b7a9b890281cd2689c9ff56ae7ec1d9c39f4a53
- Executor JSX neschimbat SHA-256: d9a704f50a9f221fb93f15884c3cda20e328d3aa0ffbd7a6cced202ebe6a52a2

## Blocante
- Test LIVE în Premiere 25.6.4 pe secvență de probă: Orange/Bold, text Unicode, 1–4 rânduri, readback real, coliziuni, rollback.
- Confirmare vizuală pe DOCX editorial real local, fără a publica documente/transcrieri.
- Pachet GitHub allowlisted cu verificare base hashes; canal beta explicit, nu stable.
- Nu promova ramura peste v1.9.13 înainte de toate criteriile P0.

**Nu este încă update instalabil. Păstrează v1.9.13 ca stable.**
