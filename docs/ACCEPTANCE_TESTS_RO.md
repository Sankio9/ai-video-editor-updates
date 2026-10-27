# AI VIDEO EDITOR — TESTE OBLIGATORII ÎNAINTE DE RELEASE

**Stare inițială (2026-10-27):** nu există încă un release validat în Premiere pentru modurile independente 02–04. Orice PASS local nu implică LIVE PASS. A se citi împreună cu `AI_VIDEO_EDITOR_MASTER_SPEC_RO.md`.

## P0 — Blocante pentru «Final»
1. Fresh project + DOCX nou; scanner recursiv Project Panel, inclusiv bins nested/offline/duplicates/conflicting codes. Testare separată import surse incorecte și situație de eroare fără schimbări în secvență.
2. 01: ASR-first fără fallback la timecode; test cu abateri ±60s, TC lipsă/IN-only/OUT-only, fraze parafrazate, repetate, intervievatori și ambianță. ZERO tăieturi pe timecode brut când ASR nu confirmă.
3. 02 STANDALONE: secvență goală, V3 existentă, V1/A1 goale, buton unic; text integral DOCX, maximum 74 caractere, 16:9, preview timing marcat clar și separator exclusiv între blocuri, fără goluri R143.
4. 03 STANDALONE: secvență goală, V4 existentă, V1/A1 goale; un MOGRT per antet editorial; nume/funcție corecte, Unicode și readback MOGRT după import.
5. 04 STANDALONE: secvență goală, V5 existentă, V1/A1 goale; DOAR cartoanele din DOCX, fără VO/montage gaps; verificare 4 rânduri x 33 caractere, Orange+Bold+Text readback.
6. 02/03/04 SYNCED: aceleași rezultate ca modulele stabile anterioare pe secvență cu montaj R143 validat.
7. Toate categoriile: preflight piste insuficiente/blocate, clipuri colizionate, secvența schimbată după verificare, același plan rulat de două ori, parțial inserat și întrerupt. Fără ștergerea conținutului neaparținând modulului. 04 V5 ocupată: inventar complet și **exact** opțiunile «Suprascrie materialele de pe V5» (consimțământ explicit distructiv) / «Oprește, eliberez V5»; nicio cale implicită de ștergere.
8. Snapshot hash clipuri/timpi V1/A1 și alte piste înainte/după fiecare operație; diferențe numai pe pista selectată.
9. CLI UTF-8 Windows, read-only progress, fără ferestre console, no START ASR at Premiere startup; DOCX change corect invalidează cache.
10. Installer check SHA-256 allowlist, both CEP roots, upgrade from last installed version, backup and rollback verificat. GitHub release public doar cu fișiere distributabile; fără DOCX, transcrieri sau source editorial privat.

## Scenarii de regresie
- «Bubuieci» 7 surse (cod corectat 9981), 19 pasaje, 8 blocuri VO.
- Erori raportate: R1.9.3 timecode fallback; R1.9.11 8/17 reject; R1.9.13 9 accept + 8 review + 2 no match; ambianță 9974 ASR corupt.
- Probe MOGRT: verificare text multilingv, NameTag de două ori pentru același nume dacă există două blocuri editoriale; 8 caption groups fără zerouri de montaj.
- Subtitrări independente nu au sincronizarea audio pretinsă; folosesc badge text «PREVIEW TIMING / nesincronizate»; pentru sync real trebuie sursă de timp verificată.

## Condiție publicare
Afișează explicit rezultatele ca [LOCAL PASS], [PREMIERE LIVE PASS], [FAIL] sau [NOT TESTED]. Release «stable/final» doar dacă toate P0 au LIVE PASS; altfel «candidate/experimental» și update-ul stabil rămâne neschimbat.


## R2.0.3 — test adăugat pentru AMB fără NameTag
- DOCX cu 8 antete de identificare și 2 CUT-uri din bloc AMB: 8 MOGRT V4, două intrări `SKIP_AMBIENCE` vizibile; fără dialog inutil de aprobare, fără identitate inventată.
- DOCX cu SINCRON fără nume/funcție: `REVIEW_MISSING_IDENTITY` și dialog explicit ÎNAINTE de inserare; la Cancel zero scrieri. Cod sursă contradictoriu => STOP.
- Verifică readback NameTag, unicitate pe bloc, păstrarea V3 (43 segmente), Unicode și caz de revenire a aceluiași speaker. Niciun rezultat mock/CI nu echivalează cu LIVE PASS în Premiere.
