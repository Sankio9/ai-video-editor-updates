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


## R2.0.3 — rezultat LIVE pentru NameTag independent (27 octombrie 2026)
- [x] Premiere: `READBACK PASS: 8 MOGRT pe V4 — EDITORIAL_PREVIEW` (screenshot utilizator).
- [x] Identificări fără NameTag: `SKIP_AMBIENCE` doar CUT-18/CUT-19 sursa 9974 (screenshot utilizator).
- [x] Program Monitor: `MĂDĂLINA CRIULEAN` / `ELEVĂ`, caractere românești afișate (screenshot utilizator).
- [x] V3 păstrată vizual, V1/A1 fără montaj, inserare independentă V4.
- [ ] Audio sync, V3/V4 aliniate pe montaj existent și regresii pe alte DOCX — NU încă validate.
- [ ] 04 Cartoane V5 LIVE — următorul test.


## R2.0.4 — Cartoane compacte & accente (TESTE DE ACCEPTARE)
- [ ] **LIVE Premiere:** secvență TEST fără 01/V1/A1 și V5 goală; generează numai cartoanele DOCX pe V5. Nicio schimbare pe V1/A1/V3/V4; MOGRT readback text + `Bold Words` + Orange.
- [ ] **LIVE vizual:** carton scurt într-un singur rând când încape, texte intermediare în numărul minim de rânduri, maxim 4×33 per pagină; fără cuvinte tăiate, spații de montaj sau deplasări neașteptate.
- [ ] **LIVE vizual:** cifre/procente și cuvinte/fraze importante evidențiate numai pe tokenurile corecte; Unicode RO (ă â î ș ț, majuscule), cifre zecimale și mai multe pagini. Revizuire editorială a accentelor — `LOCAL PASS` nu certifică selecția semantică.
- [ ] **LIVE preflight:** V5 ocupată cu MOGRT, foto sau video, la început/mijloc/final => inventar complet, **exact două opțiuni**; varianta de oprire nu schimbă timeline-ul. Ruta distructivă se testează numai dacă există rollback complet demonstrat.
- [ ] **LIVE regresie:** NameTag R2.0.3 cu `SKIP_AMBIENCE`, 02 independent și mod 01 sincronizat; nicio rescriere accidentală.
- [ ] **LIVE updater:** upgrade R2.0.3 → R2.0.4 prin Beta, manifest 2 fișiere, SHA-256, backup automat, rollback restaurând byte-exact cele două rădăcini CEP/fișierele anterioare; ZIP manual interzis. Stable nu devine R2.0.4.
- [x] **RELEASE Beta publicat**: v2.0.4, prerelease, SHA-256 arhivă `dc5fe714758ec388a18ac317b113452a33a6a65e5ae1101b7cda6c792308be9f`, 8219 octeți. **Nu este LIVE PASS**.
- [x] **LOCAL/CI:** teste sintetice layout, regresie NameTag și mock ExtendScript raportate PASS în procesul de construire; aceste rezultate nu validează ochiul editorial ori renderele Premiere.


### Evidență Premiere LIVE — captura 2026-10-27 16:18:53 (confirmare PARȚIALĂ)
- [x] **PREMIERE LIVE VISUAL:** un carton independent este redat pe Program Monitor cu 2 rânduri, diacritice RO și accente Orange/Bold efective. Exemplu vizibil: `UNII ELEVI ÎNVAȚĂ ÎN SISTEM / DUAL: ȘI LA ȘCOALĂ, ȘI LA MUNCĂ`.
- [x] **PREMIERE LIVE VISUAL:** pe pista V5 se văd opt segmente grafice în ordinea scenariului; pe V3 și V4 sunt alte clipuri, fără montaj aparent pe V1/A1. Numărul e estimat vizual; **nu reprezintă readback automatat**.
- [ ] **NECONFIRMAT:** readback numeric 8/8 MOGRT și proprietăți precise `Bold Words` / text / durate; comparația 8/8 cu DOCX, toate cele 4 rânduri, păstrarea exactă a V1/A1/V3/V4 înainte/după, V5 ocupată, anulare și rollback.
- [ ] **EDITORIAL REVIEW:** highlightul din exemplar prinde `ELEVI ÎNVAȚĂ` și `ȘCOALĂ`, dar nu prioritizează conceptul esențial `SISTEM DUAL`. Este un defect de **selectare semantică**, nu o dovadă de eroare de inserare MOGRT.
- **Stare 04:** `LIVE VISUAL PARTIAL PASS`; NU marca P0 complet și NU promova Beta la Stable.


### Evidență suplimentară LIVE — READBACK modul 04 (captura 2026-10-27 16:27:34)
- [x] **PREMIERE LIVE READBACK PASS:** panoul CEP arată explicit `[PREMIERE READBACK] READBACK PASS: 8 MOGRT pe V5 — EDITORIAL_PREVIEW` pentru 04 → Independent din scenariu → De la începutul pistei (00:00).
- [x] **PREMIERE LIVE VISUAL PARTIAL:** captura Program Monitor anterioară arată cartoanele pe V5, 2 rânduri, Orange/Bold și Unicode RO corect.
- [ ] **ÎNCĂ NECONFIRMAT:** comparație readback **conținutul fiecărui MOGRT/parametrii Bold** cu DOCX original; snapshot non-distructiv pe alte piste, V5 ocupată, cancel și rollback; accentuare semantică editorial optimă. READBACK PASS de cantitate nu dovedește aceste proprietăți.
- [ ] **UX bug confirmat vizual:** în modul Independent, încă apar controale și ajutor legacy R1.7 (ex. «Verifică rezultatul», «Generează planul R17 și apasă Verifică.»). Cerință patch: ascunde numai blocurile legacy în modul Independent și restaurează-le identic în modul «Pe montajul existent»; nu schimba executoarele MOGRT.
- **Status actual 04:** inserare și număr LIVE PASS 8/8; aspect LIVE PASS parțial; suita P0 completă încă deschisă.


## R2.0.5 Beta / CI (2026-10-27)
- [x] **GitHub Beta v2.0.5 publicată** fără a afecta canalul Stable; 2-file delta (`cep/r20_panel.js`, `tools/r204_carton_layout.py`), upgrade strict din R2.0.4.
- [x] **GitHub Actions CI PASS**, run `40553121226`: v2.0.4 exact ZIP SHA-256, testele semantic (6, incl. 200 intrări sintetice), mock UI 02/03/04, 18 mock ExtendScript, guard, două fișiere + `before_sha256` și control release Stable.
- [x] **CI branch regresii PASS**, ultimele runuri `40553391478` și `40553403216`. Eșecul precedent al testului branch era legat de `HEAD^` indisponibil în checkout shallow; a fost reparat, ulterior PASS.
- [ ] **LIVE Premiere R2.0.5 nevalidat**: restaurare controale legacy la comutare, readback al noilor evidențieri, text 8/8 și V5 ocupată, rollback real.
- [ ] **01 montaj nu e P0 PASS**: 9 accept, 8 review, 2 NO_MATCH în ultimul diagnostic R1.9.13; ASR 9974 defect. Modul 05 HOLD.
- **IMPORTANT**: Nu marca release Stable din acest CI; R1.9.13 continuă ca ultimul Stable confirmat.


## R2.0.6 — plan de retranscriere selectivă (candidate, 27 octombrie 2026)
- [x] **CI PASS:** GitHub Actions run `40555364392` — teste sintetice de alegere ferestre ASR (fără materiale private), sintaxă Python, configurare Stable neschimbată.
- [x] **Protecție:** `automaticCuttingAllowed:false`, `safeToModifyPremiereTimeline:false` în orice rezultat, inclusiv status necunoscut. Nu se aplică TC drept IN/OUT. Durată sursă/cod contradictoriu => STOP.
- [x] **Confidențialitate:** teste de ieșire fără `scriptText`, `startHeard`, `endHeard`, nume, DOCX path sau transcript. Execuția nu transcrie ori modifică Premiere, produce numai recomandări de cerere ASR locală.
- [ ] **BLOCANT:** codul `experimental/r20/r206/tools/r206_selective_asr.py` este laborator independent, **nu e conectat încă la butonul 01**. Urmează retranscriere locală efectivă pentru ferestre selectate, cache, abordare multilingual și comparație cu scenariul pe audio real.
- [ ] **BLOCANT:** confirmare în Premiere că reevaluarea celor 10 fragmente nesigure recuperează IN/OUT valide sau le lasă în REVIEW, fără tăieturi false. Acesta este P0 LIVE necesar înainte de Stable.

## R2.0.6 — executor local faster-whisper (CI, nu LIVE)
- [x] `r206_retranscribe.py` oferă procesare locală opt-in a ferestrelor ASR, cu FFmpeg/ffprobe și model CTranslate2 preinstalat; cuvintele au timp ABSOLUT față de sursă. Artefactele sunt candidate marcate `REVIEW_REQUIRED`, nu tăieturi.
- [x] 12 teste suplimentare cu FFmpeg/ASR simulate trecute în GitHub CI run `40556352429`; împreună cu 18 teste planner = 30 PASS, fără audio real.
- [ ] Benchmark/validare RTX 3070 și audio ro/ru din reportaj, quality gates împotriva halucinațiilor, mapping Project Panel offline/duplicat, apelare prin **butonul 01** și verificare LIVE Premiere (înainte de orice release stable). Nu marca R2.0.6 instalabilă.
