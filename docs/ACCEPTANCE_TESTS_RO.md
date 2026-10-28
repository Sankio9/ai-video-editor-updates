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


## R2.0.6 — Project Panel / mapping surse (CI, 27 octombrie 2026)
- [x] **CI PASS** https://github.com/Sankio9/ai-video-editor-updates/actions/runs/40558090871: 18 teste planificator ASR, 12 teste executor local, 17 teste recursive inventory și un test mock JSX read-only. **47 Python + 1 Node mock PASS**, fără Premiere LIVE.
- [x] **Inventar surse recursive** pentru orice bin, cu `ProjectItem.getMediaPath()`, `isOffline()`, `nodeId` și tip CLIP/BIN/FILE/ROOT; filtrează secvențele. Codul de 4 cifre provine exclusiv din numele media, nu din cifrele din directoare, cu detectarea codului contradictoriu display vs disc.
- [x] **Blocare conservatoare:** cod sursă lipsă -> `MISSING_RED`, multiple surse -> `DUPLICATE_RED`, offline / cod contradictoriu / media inaccesibilă -> `MEDIA_ISSUE_RED`. Rescan runner poate primi inventarul Project Panel prin `--project-inventory`, fără mapare manuală `--source-map`.
- [ ] **BLOCANT LIVE:** scannerul .jsx și adapterul local sunt pe branch candidat, **neactivate în panoul 01**; validare pe Project Panel Premiere real, offline/missing/duplicat, portarea în butonul 01, CUDA audio test și rollback rămân deschise. Niciun release R2.0.6 nu a fost publicat.


## R2.0.7 — 02 Strikethrough și incident Montaj 01 (28.10.2026)
- [x] **CI synthetic PASS:** `R2.0.7` pe branch `feature/r20-independent-graphics-gate`, 16 teste de formatare Word incl. italic, strikethrough parțial/dublu, text integral omis, ambiguitate STOP; test mock CEP cu bifa OFF implicit, Independent activă, Synced inactivă și controale legacy intacte. Rularea integrată de plan 02 din DOCX sintetic a fost adăugată în CI separat.
- [ ] **LIVE Premiere 02 Independent:** alege `Omite textul tăiat`; verifică fiecare text MOGRT + număr cues, textul italic reporter păstrat, niciun cuvânt tăiat. Încercare cu bifa OFF => include textul Word inițial. Schimbare bifă în timpul generării => STOP/rollback.
- [ ] **SYNCED 02:** integrare filter în motorul sincronizat, apoi test LIVE comparativ cu V1/A1, fără schimbarea ancorelor audio; nu aproba Stable înainte de aceasta.
- [ ] **01 Montaj incident REAL:** captura 28 octombrie 2026 a transmis `OPRIT: 8/17 sincronuri fără potrivire audio sigură`, inclusiv 9931 CUT-01/02, 9980 CUT-04, 9930 CUT-05/06, 9937 CUT-15 și 9974 CUT-16/17. Niciun clip inserat — protecția este corectă, potrivirea încă NU. Unele propoziții DOCX sunt strikethrough (ex. CUT-02), iar ultimul diagnostic complet din Library poate fi anterior testului curent: nu-l substitui pentru raportul actual.
- [ ] **01 Montaj recuperare:** probe ASR locale + ancore/parafraze real audio pentru aceste 8 CUT-uri, confirmări editorialice pentru eventuale AMB; niciodată fallback TC sau ACCEPT fals. `R2.0.6` scanner Project Panel + retranscriere selectivă sunt candidate mock CI, nu legate încă la butonul Montaj și nu LIVE.


### R2.0.7 — Beta publicată 28.10.2026
- [x] **GitHub prerelease v2.0.7** https://github.com/Sankio9/ai-video-editor-updates/releases/tag/v2.0.7; 13.961 bytes, ZIP SHA-256 `526cad27b2de0afbe3d27d920604a097e39ce9f2208c9dcf60efd9957535e622`. Upgrade strict incremental de la v2.0.5 prin Beta updater, exact 3 fișiere `cep/r20_panel.js`, `tools/r20_graphics_plans.py`, `tools/r207_docx_strike.py`, SHA before pentru cele două fișiere existente, nou helper protejat; **NU Stable**.
- [x] **CI PASS** run `40645725577`: ZIP precedent v2.0.4 și v2.0.5 verificat SHA, 16 teste DOCX, 4 teste integrative generator, 1 mock CEP, 18 MOGRT mock, guard și 12 teste NameTag. Aceste rezultate nu sunt Premiere LIVE.
- [ ] **02 LIVE**: instalare Beta și test pe copie proiect, checkbox OFF vs ON, omiterea Strikethrough, păstrarea Italic, V3 readback și rollback; numai independent. Pentru Synced filtrul trebuie integrat, nu e în Beta.
- [ ] **01 LIVE**: poza 8/17 indică încă eșec matcher, deci nu declara Montaj rezolvat după v2.0.7.


## INCIDENT LIVE 02 V3 Strikethrough 0/0 — R2.0.9
- [x] **BUG LIVE documentat** (28 octombrie 2026): checkbox ON, V3 are 43 MOGRT, Program Monitor păstrează propoziția Word tăiată, `READBACK PASS` de inserare + `Omise 0 caractere tăiate în 0 CUT-uri`; detectarea Strikethrough a eșuat. `READBACK PASS` nu certifică filtrarea textului.
- [x] **CI testat**: https://github.com/Sankio9/ai-video-editor-updates/actions/runs/40647345098 — 14 teste OOXML/style/Track Changes + 6 teste generator integrat, mock UI și mock MOGRT PASS. R2.0.9 publicată numai ca Beta: https://github.com/Sankio9/ai-video-editor-updates/releases/tag/v2.0.9, ZIP SHA-256 `2679e98ff441bc993b7e663082f4e912f47ca000f9c994ffc565da5b1e8bb2f2`, 3802 octeți. Manifest: **un singur fișier** `tools/r207_docx_strike.py`, before_sha256 `7a1db297fe2a7e8174e049d653f1ef6098704ecade8f07afe706b1c7e9607bc0`, upgrade strict v2.0.7 → v2.0.9 prin Beta updater.
- [ ] **PREMIERE LIVE RECHECK obligatoriu**: pe **copie** de secvență cu V3 goală, după update Beta v2.0.9, checkbox ON, același DOCX Bubuieci. Așteptat: fie textul marcat este eliminat cu `removedStrikeCharacters > 0`, fie STOP `STRIKETHROUGH_NOT_DETECTED` înainte de inserare; niciodată 43 MOGRT cu 0 omisiuni și `READBACK PASS` fals. Verifică în Program Monitor fraza `Vreau să mă dezvolt...` și păstrarea întrebării italice. Nu șterge V3 existentă automat.
- [ ] Dacă încă apare `STRIKETHROUGH_NOT_DETECTED`, este necesar **DOCX-ul original** pentru inspecție locală a markup-ului Word; screenshotul nu dovedește dacă linia este `w:strike`, Track Changes sau un element desenat. Nu publica materialele editoriale în GitHub public.


## R2.1.0 — acceptare analiză DOCX înainte de V3 (28 octombrie 2026)
- [x] **BETA publicată** https://github.com/Sankio9/ai-video-editor-updates/releases/tag/v2.1.0; ZIP 13840 bytes, SHA-256 `287eabc714e853ec6d6d2d7504abe8225a5c326fc5dea88c973f6c68f7145be2`; prerelease incremental strict de la v2.0.9, numai `cep/r20_panel.js` + `tools/r20_graphics_plans.py`, cu sha256 `before_sha256` pentru ambele. Stable rămâne R1.9.13.
- [x] **GitHub Actions CI PASS** run `40649698809` (publish), `40649502941` și `40649631283` (two-phase): 14 teste stil OOXML și tracked-deletions, 9 teste plan DOCX, UI mock și flux mock async cu analiza→preview→validare, zero-omission fail, motor învechit fail, DOCX schimbat fail, bifa schimbată fail, plus MOGRT guards și NameTag regresii. NU este test LIVE.
- [ ] **LIVE P0 Bubuieci:** pe **copie secvență cu V3 goală**, după update R2.0.9 → R2.1.0 prin Beta, selectează în 02 Independent, bifa ON, click `1 · Analizează DOCX`. Program Monitor/timeline nu trebuie schimbate. În preview verifică `CUT-02`: `Vreau să mă dezvolt în profesia dată.` trebuie lipsă din `DUPĂ`, dar întrebarea în italic și răspunsul trebuie păstrate. Dacă scannerul nu poate face asta, trebuie STOP explicit și raport de format; nu considera funcțională.
- [ ] **LIVE P0 inserare:** doar după preview aprobat, `2 · Inserează subtitrările verificate pe V3`; textul MOGRT exact ca `DUPĂ`, `READBACK` verificabil, piste V1/A1/V4/V5 nemodificate și preflight V3 ocupată.
- [ ] **LIVE P0 installer:** confirmă din panou că motorul/CEP sunt ambele R2.1.0, inclusiv în ambele rădăcini CEP; hash-mismatch nu permite generare. Înapoi la R2.0.9 cu rollback byte-exact.
- [ ] Dacă DOCX real nu se poate analiza, cere **originalul DOCX în acest chat** pentru inspectarea w:strike/w:dstrike/Track Changes; screenshot nu dovedește structura internă. CI nu poate substitui acest test.


## R2.1.1 — Subtitle UX polish și reguli de împărțire (Beta 2026-10-28)
- [x] **Utilizator R2.1.0:** filtrarea Strikethrough a funcționat efectiv (confirmare din utilizator). Screenshotul nou arată o subtitrare care termină cu `Să` după `...planul de admitere.`, caz vizual neplăcut.
- [x] **CI synthetic PASS**: branch `feature/r20-independent-graphics-gate`, test `40652478230` după corecția pragului de despărțire: DOCX parser/strike, 74 caractere, întreaga frază restaurată identic, început de propoziție la următorul MOGRT, ~200 intrări sintetice repetitive, panou cu un singur buton și mock Premiere care dovedește nicio comandă înainte de analiza Word, STOP zero-omision, STOP motor vechi, STOP document/bifă schimbată.
- [x] **Beta v2.1.1 PUBLICATĂ:** https://github.com/Sankio9/ai-video-editor-updates/releases/tag/v2.1.1, ZIP 14117 octeți, SHA-256 `f0a088d7954b09664706e66eb10abb9cf17fa3726eef52fe5639d7ce486b0a12`; upgrade strict v2.1.0 → v2.1.1 prin updater Beta, delta 2 fișiere `cep/r20_panel.js` + `tools/r20_graphics_plans.py`, ambele cu `before_sha256`. CI publicare `40652619521` PASS; stable R1.9.13 neafectată.
- [ ] **LIVE Premiere:** pe COPIE secvență cu V3 goală, după update R2.1.1, 02 Independent afișează un singur buton `Inserează subtitrările` și bifa; la ON rezultatul nu include text Word tăiat, iar fraza `Să informăm tinerii că...` începe o subtitrare nouă, nu încheie subtitrarea precedentă cu `Să`.
- [ ] **LIVE safety:** schimbarea bifei/DOCX în timpul procesului, V3 ocupată, rollback, durate, readback conținut pentru toate cues și lipsa modificărilor V1/A1/V4/V5. Mock CI PASS nu substituie acest test.


## R2.1.2 — echilibru și feedback învățare (28 octombrie 2026)
- [x] **LIVE R2.1.1 parțial confirmat de utilizator:** propoziția `Să informăm...` a trecut la următorul MOGRT, dar continuarea a fost `... dar să` / `nu stea acasă.`, deci lizibilitatea necesită optimizare.
- [x] **CI synthetic PASS:** run `40665188788` și `40665295052`: 20 teste generator/segmentare (inclusiv exemplul 41/34 și excepția propoziției scurte, 300 intrări aleatorii), 14 teste Word OOXML/Strike, mocks CEP one-click, MOGRT, guard, NameTag; compilare Python. Include test de contiguitate după `planul de admitere.` și exact DOCX text cu punctuație.
- [x] **Beta publicată:** https://github.com/Sankio9/ai-video-editor-updates/releases/tag/v2.1.2, ZIP SHA-256 `e5a0a277fd13834acba3712eacec82a9f9eeaa05887668458c124797c6e89f4e`, 7551 octeți. Update incremental strict v2.1.1 → v2.1.2: UN SINGUR fișier `tools/r20_graphics_plans.py`, `before_sha256` verificat. Stable v1.9.13 nemodificată.
- [ ] **LIVE Premiere R2.1.2 obligatoriu:** pe COPIE secvență cu V3 liberă, 02 Independent, un singur buton + bifa, DOCX Bubuieci. Verifică 41/34 pe propoziția `Să informăm...`, lipsa resturilor mici, respectarea punctuației și textului integral; nu suprascrie V3 existentă. READBACK, coliziuni, rollback trebuie confirmate LIVE.
- [ ] **„Buton magic” viitor, nu livrat:** read-only snapshot/compare AI-plan vs editări reale editor, propuneri diferențe cu dovezi și **Aprobă/Respinge/Amână** separat; niciun auto-learning fără aprobare. Specificație în `docs/EDITOR_FEEDBACK_LEARNING_SPEC_RO.md`; necesită test LIVE că MOGRT text/timp/stil pot fi citite în mod sigur.


## R2.1.3 — Montaj ASR Recovery Beta (28 octombrie 2026)
- [x] **GitHub CI PASS:** https://github.com/Sankio9/ai-video-editor-updates/actions/runs/40667033655 — 18 teste sintetice potrivire expresie unică, RO diacritice, start/end real, repetări, TIMEcode fără audio, lipsă parole și drift >75 s; teste R2.0.8 pentru 8 CUT-uri din 5 surse. Construirea pipeline-ului din arhiva originală R1.9.13 cu checksum exact `9ab648fd3472d0a13ce7cb815e953894d961fcc2ea9113f250099720dabb1034`, pipeline before SHA `8b49231f2c534f87ac2486f407fbc4466b1a2c77ee99961d0ed17d500959080e`, validată.
- [x] **BETA publicată** https://github.com/Sankio9/ai-video-editor-updates/releases/tag/v2.1.3; ZIP SHA256 `5cb8fd4e65ecc77d148aa78a5c98eaff5cf13c1977ed84537f52f5991d257ffd`, 8027 bytes, doar două fișiere `tools/r193_pipeline.py` + `tools/r213_second_pass.py`. Delta strictă de la R2.1.2 Beta, Stable R1.9.13 nemodificată. CI publish https://github.com/Sankio9/ai-video-editor-updates/actions/runs/40667140553 SUCCESS.
- [ ] **LIVE Bubuieci:** utilizatorul actualizează prin Beta updater la v2.1.3, pe o COPIE a secvenței, apasă `Montează după scenariu` și verifică numărul de CUT-uri ACCEPT/REVIEW; urmărește V1/A1. Dacă 8/17 rămâne ori scade incomplet, cere diagnosticul NOU `D:\AI-Video-Editor\Temp\R193\last_match_diagnostic.json`, nu documentul vechi cu 19 CUT-uri. Nu promova Stable fără rezultate reale.
- [ ] **P0 selector audio real:** R2.1.3 reanalizează cuvintele ASR deja transcrise, **nu retranscrie local audio din nou**. Pentru audio lipsă/transcris slab, trebuie integrat laboratorul R2.0.6 cu preflight surse și ferestre, re-ASR pe RTX3070, validare dialog unic și limite IN/OUT înainte de plan.


## R2.2 — avertizare/editorial missing clips (cerință pentru Beta)
- [ ] Când un script are 19 CUT-uri, 9 validate și 10 review, analiza arată lista completă de 10 înainte de aprobare, fără a scrie timeline-ul.
- [ ] După continuarea aprobată și readback, panoul 01 afișează `Montaj parțial: 10 sincronuri de verificat`, cu listă disponibilă după închiderea dialogului și reîncărcarea extensiei.
- [ ] Fiecare rând: `CUT / cod sursă / nume fișier dacă disponibil / motiv exact / poziție și durată estimată / status`. Distingem media absentă de ASR eşuat şi de timecode incert; două CUT-uri din același fișier nu sunt prezentate ca două fișiere distincte lipsă.
- [ ] Rezultatul de inserare se raportează numai după readback; REFUZUL => zero modificări/zero mesaj de succes.
- [ ] Navigarea la marker este read-only; raport JSON local atomic, legat de seqId+hash, persistent, fără conținut editorial privat în GitHub.
- [ ] Fără buton suplimentar de montaj. Unicul `Montează după scenariu` + dialog contextual la probleme; altfel automat.


## R2.2 — planner sintetic implementat (28.10.2026)
- [x] `experimental/r20/r220/tools/r220_montage_plan.py` pe `feature/r20-independent-graphics-gate`, `PLAN ANALYSIS_ONLY`: nu permite modificarea Premiere. CI run `40726539952` SUCCESS, 19 teste sintetice nou-adăugate pentru statusuri, surse, durate, plan hash, decizie explicită, raport lipsuri, readback și confidențialitate; plus regressions R2.1.3/R2.0.8.
- [x] 19 CUT-uri sintetic -> 9 validate/10 placeholders. Două sincronuri cu sursa 9974 ONLINE sunt `AUDIO_NOT_FOUND`, nu două fișiere distincte pierdute; dacă 9974 MISSING, raportul conține un singur cod de sursă distinct lipsă.
- [x] `AI_MATCHED` fără validator nu devine clip. Timecode de 1 sec pentru o declarație lungă nu determină tăierea. Plan mutat/sequence ID schimbat/refuz user blochează orice autorizare.
- [ ] **NU ESTE LIVE**: scanner Project Panel, mapping pe montajul DOCX real, dialogul contextual, slot marker Premiere V1/A1, backup/rollback, citirea după inserare și persistent notification în panou încă neimplementate. Nicio versiune R2.2 Beta de instalat. Stable R1.9.13 păstrată.
