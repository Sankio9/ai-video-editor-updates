# AI Video Editor — CONTINUARE ÎN CHAT NOU

**Instrucțiune:** „Continuăm AI Video Editor — Reportaj. Citește `docs/AI_VIDEO_EDITOR_MASTER_SPEC_RO.md`, `docs/ACCEPTANCE_TESTS_RO.md` și acest fișier din `Sankio9/ai-video-editor-updates`. Verifică ultima versiune GitHub REALĂ și evită să confunzi candidaturile locale cu release-urile publicate. VO rămâne pe HOLD.”

## Ce este stabilit
- Windows Premiere 25.6.4, CEP/ExtendScript, `D:\AI-Video-Editor`, faster-whisper CUDA, un DOCX în 00, Project Panel recursiv.
- 01 audio-first, fără fallback la TC; uneori diferență ±30-60 s; fără TC dacă video <=8min, cu TC parțial căutare extinsă după text.
- 02 V3, 03 V4, 04 V5 funcționează **independent fără 01**, ori sincronizate la montaj existent. În independent folosesc doar spații scurte între blocuri, nu gaps montaj. Subtitrări independente = PREVIEW TIMING dacă lipsește sincronizarea audio. Fiecare categorie un singur buton.
- Protecție V5 exact două alegeri pentru materiale existente. Fără QE addTracks, fără overwrite implicit; rollback obligatoriu.
- Lansare Premiere: toate accordeoanele închise, zero ASR la startup, progress global și cache persistent cu TTL configurabil; țintă sub 60 s numai după preanaliză.
- Surse lipsă marcate roșu, coduri multiple/contradictorii -> stop; UTF-8 obligatoriu.
- Repo GitHub PUBLIC doar actualizări și documentație neutră, fără scenarii, transcripturi sau surse editoriale private.

## Ultimul test real cunoscut
Pe «Bubuieci», R1.9.13 a refuzat montajul pentru 10/19 sincronuri (9 accept, 8 review, 2 NO_MATCH). 9974 în ASR este grav defect, transcrierea trebuie reevaluată selectiv; utilizatorul a transmis un ZIP cu transcrieri locale doar în chat, NU în GitHub. **Nu reduce praguri pentru a forța montajul.**

## Stare tehnică / ce este de făcut
- R1.9.13 era ultimul release stabil verificat la redactarea inițială. Verifică exact API-ul GitHub releases/latest înainte de orice afirmație.
- R1.9.14 ASR Audit Lab este diagnostic local; nu update de producție.
- Prototype standalone plans de separat pe categorii există local dacă aceeași sesiune/container: `/mnt/data/aive_final_audit/r20_independent_plans.py`, clone JSX `/mnt/data/aive_final_audit/candidate/cep/jsx/`. NU considera acest prototip testat în Premiere și NU publica clonele legacy nemodificate în repo-ul public.
- Următoarea lucrare: integrare CEP standalone mode / preflight / real MOGRT / progres / profil/cache, apoi teste local + live în secvență goală și rollback.
- Nu cere din nou întrebări deja clarificate. Verifică via connector GitHub înainte de publicare.

## Checkpoint implementare R2.0, 2026-10-27 (continuare după sursele locale)

- Utilizatorul a furnizat arhiva de colectare a codului instalat: `AIVE_R20_SOURCE_ONLY_20261027_133924.zip`. Au fost auditate 60 de fișiere, 59 păstrate byte-identic; numai `cep/index.html` este modificat între sursele existente. **Arhiva colectată NU conține DOCX, media sau MOGRT**.
- Sursele noi pentru candidatul standalone R2.0 sunt păstrate în ramura `feature/r20-independent-graphics-gate`, PR [#1](https://github.com/Sankio9/ai-video-editor-updates/pull/1), la `experimental/r20/candidate/`: `cep/index.html`, `cep/r20_panel.js`, `cep/jsx/r20_graphics.jsx`, `tools/r20_graphics_plans.py`, teste mock.
- Implementat local: selector modul existent/independent în CEP, planificare DOCX fără R143 pentru 02–04, preview timing explicit, distanțe scurte între blocuri, inserare `importMGT` cu parametri MOGRT + readback, verificare coliziuni/locked/sequence change, rollback al MOGRT-urilor nou inserate, protecție V5. **Overwrite destructiv V5 este încă blocat intenționat în standalone**, până la test/backup LIVE.
- Teste executate: **7 Python planner PASS; 18 mock JSX PASS; 4 updater SHA/dual CEP roots/rollback PASS**. Workflow GitHub Actions pentru mock JSX a trecut. Acestea sunt **LOCAL PASS**, nu `PREMIERE LIVE PASS`.
- Pentru release este necesar să se pregătească pachetul updater bazat pe hash-urile versiunii R1.9.13, cu integrare surse candidate, apoi un opt-in LIVE TEST pe proiect duplicat. `release/next.json` și release-ul stabil v1.9.13 rămân neatinse. Nu publicați R2.0 ca stabil înainte de P0 LIVE PASS.
- Într-un chat nou, **recuperați direct codul din PR #1**, nu reconstruiți din memorie. Generatorul nou încă nu a fost testat pe DOCX-ul Bubuieci real, care nu era în arhiva de surse.

- **Ultimul candidat CI:** run GitHub Actions `40501323141` pe PR #1 **SUCCESS**; sunt verificate mock JSX și build-ul de pachet candidat cu hashuri fixe, fără publicare în Releases. Un eșec la readback final declanșează acum încercarea de rollback a inserărilor sesiunii; test real Premiere încă necesar.


## 2026-10-27 — R2.0 LIVE test handoff (după creare proiect test)
- Proiectul/secvența de test Premiere au fost create de utilizator; acest lucru NU reprezintă încă test de inserare MOGRT.
- [R2.0 pre-release experimental](https://github.com/Sankio9/ai-video-editor-updates/releases/tag/v2.0.0) este publicat prin workflow GitHub separat, din commit înghețat `7f35a35058bb97f7925ba35e88a05ae9f39ed4ae`; testele CI/mock au trecut. **Nu e Latest stable** și updaterul standard nu îl oferă automat.
- Latest stable v1.9.13 a fost re-verificat DUPĂ publicarea experimentală.
- Asset R2.0 `AIVE_UPDATE.zip`, 18185 bytes, SHA-256 `1d326ac503a658fb1725acb866d8ac3bd6b3a812288f3ac4d474c78bdbbc0003`. Are exact patru fișiere: `cep/index.html` cu before SHA obligatoriu, `cep/r20_panel.js`, `cep/jsx/r20_graphics.jsx`, `tools/r20_graphics_plans.py`.
- Lansatorul de test one-click a fost creat ca `AIVE_R20_Test_GitHub.cmd` în chatul curent. El NU este arhiva update de instalat manual: verifică release-ul prerelease/pinned digest, folosește `updater/runner.py` existent (hash controlat), `prepare()` cu staging + verificare de hash și instalare doar după închiderea Premiere. La relansare după instalare oferă rollback `2.0.0 -> 1.9.13`, Premiere închis.
- Intervenția utilizatorului: descărcarea lansatorului, dublu-click, acceptarea testului și închiderea Premiere, apoi redeschiderea pe secvența de probă. Testul inițial: secțiunea 00 selectează DOCX, 02 selectează Independent din scenariu, V3 goală, generează. Fotografia/mesajele de status stabilesc următoarea corecție.
- **Status**: încă [PREMIERE LIVE NOT TESTED]. Este interzisă promovarea ca stable, fuziunea PR #1 sau testele pe producție până la testele P0 LIVE. 05 VO rămâne HOLD. V5 overwrite destructiv este dezactivat preventiv în modul independent.

## 2026-10-27 — Hotfix pentru lansatorul beta R2.0
- Primul test de lansare pe Windows s-a oprit corect **înainte de instalare**. Mesaj: `Versiune locală neașteptată: v1.9.13. Este permis doar upgrade direct din R1.9.13.`
- Cauză: comparare literală greșită între `v1.9.13` (updater/state.json local) și `1.9.13` (lansatorul beta), deși `updater/runner.py` acceptă ambele formate.
- Lansator corectat: `AIVE_R20_Test_GitHub_FIX_v1_1.cmd`, livrat în conversație; SHA-256 `46c8ee8ed5ba39b0c8733d18646f35c4036bdaa3b8bc629e138defd5bb6e03ff`.
- Fix: compară numeric `runner.ver(current) == (1,9,13)` și la rollback `runner.ver(restored_version) == (1,9,13)`; acceptă formele cu și fără `v` pentru R1.9.13/R2.0.0. Alte versiuni rămân blocate.
- Teste locale PASS: sintaxă Python, variante `v1.9.13`/`1.9.13`, rollback pentru `v2.0.0`/`2.0.0`, refuz altor versiuni, pin SHA updater și release neschimbate.
- **Nu este test LIVE Premiere**; instalarea completă încă necesită confirmarea utilizatorului și verificările de preflight de hash pe ambele rădăcini CEP. Nu rula vechiul lansator.

## 2026-10-27 — Primul test real independent 02 (Premiere R2.0)
- Utilizatorul a instalat R2.0 beta și a raportat panou CEP funcțional în Premiere 25.6.4. Secvența de test a fost creată separat; V1/A1 fără montaj necesar.
- Modul 02 setat `Independent din scenariu`, poziție `De la începutul pistei (00:00)`. Screenshot al panoului afișează exact `[PREMIERE READBACK] READBACK PASS: 43 MOGRT pe V3 — SCRIPT_PREVIEW`.
- Codul `experimental/r20/candidate/cep/jsx/r20_graphics.jsx` confirmă că funcția `verify()` controlează numărul clipurilor, start/end, raportul 16:9, textul MOGRT și Font Style, nu doar afișează un mesaj static. Statut: **PREMIERE READBACK PASS** pentru modul 02; **validarea vizuală în Program Monitor și verificarea timeline-ului încă PENDING**.
- Defect UI identificat în screenshot: în modul Independent rămân afișate controalele legacy `Verifică rezultatul`, `Selectează planul R1514 și apasă Verifică` și labelul vechi `R1.5.15`. Acestea aparțin traseului synced/legacy; nu trebuie acționate ca verificare a inserării R2.0. Candidatul UI următor trebuie să ascundă controalele/instrucțiunile legacy doar când modul=independent și să le restabilească în synced; nu schimba motorul validat.
- Următoarea acțiune indispensabilă a utilizatorului: screenshot cu timeline-ul V3 (MOGRT, gap-uri/grupuri) și Program Monitor la moment cu subtitrare; verifică rendering/diacritice, nu doar readback API.
- Niciun test LIVE 03/04 completat. 05 VO HOLD. Stable v1.9.13 neatins.

## 2026-10-27 — Confirmare vizuală PREMIERE LIVE pentru 02 independent
- Utilizatorul a transmis captură reală Program Monitor + timeline, apoi a confirmat explicit: „arata bine, am verificat. mai tirziu vom introduce o regula noua pentru subtitrari”.
- Program Monitor afișează efectiv subtitrarea română cu diacritice („Vreau să fiu bucătar deoarece am privit un serial”), alb pe negru. Pe V3 sunt segmentele MOGRT generate, iar V1 și A1 sunt vizibil goale. Panoul a raportat anterior „READBACK PASS: 43 MOGRT pe V3 — SCRIPT_PREVIEW”.
- Status: **02 INDEPENDENT – PREMIERE LIVE PASS inițial pentru inserare/readback/render vizual**, pe secvență de test; NU echivalează cu toate criteriile P0 (regresii, 02 SYNCED, cross-DOCX, toate textele etc.). Urmează 03 NameTag independent V4, apoi 04 Cartoane independent V5.
- Utilizatorul dorește o **regulă nouă pentru subtitrări mai târziu**; conținutul regulii nu a fost încă furnizat. Nu inventa și nu modifica 02 până la specificare. Nu strica testul pozitiv.

## 2026-10-27 — R2.0.1 NameTag independent hotfix
- **First PREMIERE LIVE 03 FAIL (before MOGRT insertion):** User clicked `Generează V4 din DOCX`, generator raised `ValueError: NameTag: nu găsesc un antet editorial pentru 5` at `tools/r20_graphics_plans.py` line 92. Control stopped before `validate/buildOne`; no NameTag was inserted by this attempted operation. Screenshot showed legacy controls remain visible in independent mode.
- Root cause: the R2.0.0 planner used only standalone 4-digit **bold paragraph** from `source_headers()`, or paragraphs starting with `SINCRON:/AMB:` where header index must be strictly less than the speech paragraph index. This fails for combined logical lines in the same paragraph and for missing separate headers.
- **Fix R2.0.1:** isolated one-file replacement `tools/r20_graphics_plans.py`, markers parsed from logical lines `SINCRON/AMB` or isolated 4-digit codes, inclusive paragraph comparison, otherwise contiguous speaker/source identity blocks. Reintroduced identical identity after a new header or intervening speaker yields a new NameTag. Contradictory source code -> REVIEW, no guessed names/roles. Existing modules 01, 02 (V3), 04 and 05 and CEP/MOGRT executor unchanged. Local DOCX tests 12 PASS; isolated CI 5 tests PASS plus 18 MOGRT mocks.
- `v2.0.1` published as **experimental GitHub pre-release**, not Latest. R1.9.13 remains stable. Release asset `AIVE_UPDATE.zip`: SHA-256 `1cdad1065e5c5d92992f057b37702f923b3b3bb3f33cab1396cc14e5b69657cf`, contains **one** path with `before_sha256=37ec5e19ae2223d079263cbac9763fe2cb915593f9d4e37151cff7d522fa562f`, `after_sha256=df0b5f4ab1aa87274305222e51ea02b5adc44b26b72d72155ce38e4a2d52c9af`. Release CI SUCCESS. Local simulated updater install `2.0.0 -> 2.0.1` and byte-exact rollback PASS.
- Delivered **opt-in GitHub updater launcher** `AIVE_R201_NameTag_Hotfix_GitHub.cmd` via user chat. Its SHA-256 `b1c86e231f5f2cc08cbdc37cae2e0a11f2e527f517c5f94630f408df1ca034c2`. It calls the existing audited `updater/runner.py`, requires current 2.0.0, pins official asset SHA-256, validates one original planner file hash, stages only with backup/rollback and applies after Premiere closes. Re-running on 2.0.1 offers restore to 2.0.0 when Premiere is closed. No manual ZIP needed.
- **Awaiting user LIVE test on real Bubuieci DOCX:** after installing hotfix, 03 Independent > V4 zero > Generate. Expected 8 NameTags based on earlier prototype counts, but count/coverage must be confirmed in Premiere; this hotfix is NOT yet Premiere-validated. If still an error, request exact message/screenshot and correct surgically. The prior V3 43 subtitles remain unmodified. VO 05 HOLD; V5 standalone pending.

## 2026-10-27 — R2.0.2: Beta channel from within Premiere (one-time bootstrap)
- User requested no more separate .cmd launchers for every update; aim is in-app Stable/Beta selection with Stable default, SHA-256 and rollback.
- Existing R2.0.0 updater has NO Beta discovery and `/releases/latest` only returns stable v1.9.13. A single bootstrapping action is unavoidable without incorrectly promoting beta to stable.
- Pre-release [v2.0.2](https://github.com/Sankio9/ai-video-editor-updates/releases/tag/v2.0.2) PUBLISHED and GitHub Actions SUCCESS (run 40513921984), source pinned at `877e4c42c09b3aa0cca71d3bda26ff1b7850cc08`. Four-file delta strictly from installed v2.0.0: `cep/index.html`, `cep/aive_updater_beta.js`, `updater/beta.py`, `tools/r20_graphics_plans.py`; includes both Beta selector and R2.0.1 NameTag parser hotfix. No changes to legacy updater engine or MOGRT insertions. SHA-256 ZIP `11f1a7e68925c23786d9a926b2a960aed913b5f7daab117e918bd8fce1189463`, size 12614 bytes.
- R2.0.2 remains prerelease; v1.9.13 remains latest stable. Tests GitHub (NameTag synthetic, beta option/digest/URL, source hashes, JS syntax) PASS. Premiere LIVE for R2.0.2 pending.
- Generated **ONE-TIME** bootstrap for initial bridge: `AIVE_R202_Activeaza_Beta_O_Singura_Data.cmd` available in this conversation (file created/verified in /mnt/data). Launcher SHA-256 `e6b5b9bdc57398660a77dc8d5efcc3d5f06e03f42eb390d67c84d1675995e0ce`. It requires local installed v2.0.0, both CEP indexes matching R2.0.0, R2.0 original NameTag planner; checks runner.py SHA, GitHub latest stable/prerelease metadata/digest; calls unchanged local runner.prepare() which backs up and auto-applies only after Premiere closes. For rollback: same launcher when 2.0.2 already installed, explicit double confirmation, Premiere closed and recognized backup. Do not run if installed version !=2.0.0.
- After 2.0.2 installed: open Premiere, Extensions AI Video Editor, updater section, select Beta to check/install following v2.x releases. No need for any launcher for subsequent beta releases; stable remains default.
- Next LIVE test after bridge: `03 NameTag Independent V4`, currently V3 subtitles (43) LIVE PASS, V4 NameTag failed safely before write on old 2.0.0 due to paragraph 5 header issue. Confirm NameTag count and text/readback in Premiere and visuals, then module 04 V5.
- Do not label R2 stable/final before full P0. VO 05 remains HOLD.


## 2026-10-27 — R2.0.3 NameTag AMB skip + Beta release (status)
- În Premiere R2.0.2, modulul 03 independent s-a oprit înainte de V4: `NameTag incomplet: 2 identificări fără nume/funcție` (fără MOGRT inserate pe V4). La R2.0.0 a fost inițial `nu găsesc antet editorial pentru 5`, deja remediat în R2.0.2.
- Scenariul DOCX anterior a fost inspectat **privat** prin căutare în Library: cele două pasaje fără nume/funcție sunt blocuri **AMB** (ambianță editorială, sursa de test 9974), nu persoane pentru NameTag. NU urca DOCX-ul și nici textul real în repository.
- Regula R2.0.3: `SKIP_AMBIENCE` automat numai dacă există antet AMB explicit și cod sursă compatibil; afișează fiecare CUT omis în rezultatul permanent. `REVIEW_MISSING_IDENTITY` pentru orice alt sincron fără nume/rol => consimțământ explicit ÎNAINTE de orice inserare; refuz -> zero modificări pe V4. Codurile contradictorii -> STOP. NICIODATĂ inventare de nume/funție.
- Se așteaptă **8 NameTag-uri valide** și **2 fragmente AMB excluse**; acest rezultat nu este încă PREMIERE LIVE confirmat, doar simulator/mocks + CI PASS pe cazuri sintetice (inclusiv analog al scenariului).
- [v2.0.3 Beta prerelease](https://github.com/Sankio9/ai-video-editor-updates/releases/tag/v2.0.3) PUBLICAT, branch source fixat la `6a4be13ea04efcb6fb7fd09286fbdb658df6661a`, GitHub Actions PASS (regresii + verificare checksum), ZIP SHA256 `f44b227d9db486571cba12696ae7953485937a369f06f9eabc282159fc14342f`. Exact două fișiere, `cep/r20_panel.js` și `tools/r20_graphics_plans.py`, cu `before_sha256` pentru R2.0.2. **R1.9.13 rămâne latest stable**.
- Următorul pas pentru utilizator: În Premiere, secțiunea Actualizări > selector **Beta** > `Verifică actualizări Beta` > `Descarcă și pregătește Beta`; Salvează proiect TEST / închide Premiere / redeschide. Nu există nevoie de CMD/ZIP manual. Apoi 03 pe V4 goală; verifică mesaj `PREMIERE READBACK`, lista `SKIP_AMBIENCE`, afișare Program Monitor, păstrarea V3 cu 43 subtitrări.
- R2.0.3 NU e certificată stable, LIVE test V4 pending. 04 V5 next; 05 VO HOLD.


## 2026-10-27 — R2.0.3 Modul 03 LIVE PASS (NameTag Independent V4)
- Utilizatorul a transmis două capturi Premiere Pro 25.6.4 după instalarea R2.0.3 Beta, una cu Program Monitor + timeline V3/V4, alta cu panoul CEP și mesajele de verificare.
- Mesaj exact în panou: `[PREMIERE READBACK] READBACK PASS: 8 MOGRT pe V4 — EDITORIAL_PREVIEW`.
- Alte mesaje: `[SKIP_AMBIENCE] 2 fragmente fără NameTag`, `CUT-18 (paragraful 24, sursa 9974)`, `CUT-19 (paragraful 24, sursa 9974)`. Deci 8 NameTag-uri și 2 replici AMB corect omise, fără nume inventate.
- Program Monitor afișează efectiv `MĂDĂLINA CRIULEAN` / `ELEVĂ` cu diacritice. Timeline V4 = 8 elemente; V3 = subtitrările 43 anterioare, vizibil păstrate; V1/A1 goale. **LIVE PASS pentru inserare, readback și verificare vizuală de bază** în modul independent, nu pentru sincronizare audio.
- În Program Monitor NameTag `MĂDĂLINA CRIULEAN` apare simultan cu subtitrare din alt fragment. Acest lucru este de așteptat în modul INDEPENDENT unde V3 și V4 își construiesc fiecare timeline orientativ în mod separat; nu le prezenta drept sincronizate. În modul PE MONTAJ existent sincronizarea rămâne un obiectiv separat nevalidat.
- UI de curățat ulterior: când este selectat Independent, controalele/hint-urile legacy R1.6.2/R161 să fie ascunse, iar când e selectat Pe montaj existent să fie restaurate; NU schimba motoarele validate în același patch.
- Urmează 04 Cartoane Independent V5 pe secvența TEST, V5 verificată goală, poziție 00:00, readback/carton vizual, păstrare V3 și V4; regula exact două opțiuni pentru V5 ocupată rămâne obligatorie. 05 VO HOLD; R1.9.13 stable neafectat.

## Checkpoint R2.0.4 — Cartoane compacte & accent semantic (27 octombrie 2026)
- Codul real R2.0 a fost recuperat din pachetul local SOURCE-ONLY; fără reconstruirea prototipului. Am introdus în generatorul independent 04 modulul aditiv r204_carton_layout.py: minimum rânduri fezabile, maxim 4×33, text DOCX integral, accentuări locale deterministe pentru numere/procente/unități/termeni relevanți și indicii Bold Words corecți pe fiecare rând. Color Scheme Orange rămâne în template. Nu se modifică 01/02/03/05 și nu se activează suprascrierea V5.
- Dovezi locale: 7 teste generator + 11 layout + 18 Premiere mock + 4 updater SHA/rollback = 40 LOCAL PASS; sintaxă JSX/Python PASS. Nu echivalează cu Adobe Premiere LIVE PASS.
- Branch experimental: feature/r20-independent-graphics-gate, cu experimental/r20/tools/r204_carton_layout.py, INTEGRATION_R204.patch și R204_CHECKPOINT_RO.md. SHA plan local c89e40ec345b51fb5a44f46fdad69b6d088371492e544da2ac1dbee385f8de0d; helper local caceca0f2d1f99729c7c18ae8b7a9b890281cd2689c9ff56ae7ec1d9c39f4a53.
- Blocant de distribuție: test real în Premiere 25.6.4 pe proiect/secvență de probă (Unicode, aspect și culoare, V5 liberă/ocupată, readback, rollback). Fără update public stabil până la acceptare. Ultimul release stabil verificat rămâne v1.9.13.

## R2.0.4 Beta PUBLICAT (2026-10-27)
- GitHub prerelease confirmat: https://github.com/Sankio9/ai-video-editor-updates/releases/tag/v2.0.4 (NU latest stable); asset AIVE_UPDATE.zip, 8219 octeți, SHA-256 dc5fe714758ec388a18ac317b113452a33a6a65e5ae1101b7cda6c792308be9f.
- Upgrade incremental **numai de la R2.0.3** prin updater Beta existent în Premiere. Manifest exact două fișiere: tools/r20_graphics_plans.py (before_sha256 60b60012536cef103094ed33d2f31c05a9aec10a6bcbeb2149bca0c7c89a6698) și tools/r204_carton_layout.py (nou).
- Sursa frozen pe commit bc2eea471a072aeffdcdb6a5636ae2e9ee2c573b din feature/r20-independent-graphics-gate; workflow .github/workflows/r204-cartoane-prerelease.yml; request release/r204-cartoane-request.json. Păstrează R2.0.3 NameTag review gate.
- LOCAL: 22 teste Python + 18 mock Premiere PASS; GitHub Actions a publicat doar după teste sintetice layout, regresie NameTag R2.0.1/R2.0.3, mock MOGRT și manifest SHA. NU echivalează cu test LIVE Adobe Premiere.
- Nou modul 04: rânduri minimum fezabil (maxim 4×33), Orange/Bold semantic pentru cifre/procente/termeni, text editorial neschimbat, timing EDITORIAL_PREVIEW, fără goluri de montaj. Modulele 01/02/03/05 și executorii MOGRT nemodificați; V5 ocupată rămâne non-distructiv.
- NEXT: Premiere 25.6.4 pe COPIE proiect/secvență TEST, actualizare prin Beta și validare 8 cartoane, Orange/Bold, Unicode, readback, V5 ocupată, rollback, piste neatinsese. Stable rămâne v1.9.13.

## REGISTRU R2.0.4 — reguli înghețate și regresie extinsă (2026-10-27)
- REGULI NORMATIVE scrise în docs/AI_VIDEO_EDITOR_MASTER_SPEC_RO.md: text DOCX păstrat, layout în **numărul minim fezabil de rânduri** (max 4×33), Orange/Bold doar pe fragmente originale cu accent semantic moderat și indici MOGRT 1-based pe fiecare rând, review editorial, separatoare scurte, fără goluri de montaj/ASR în 04 Independent, V5 protejată și 01/02/03/05 neatinse.
- CRITERII LIVE scrise în docs/ACCEPTANCE_TESTS_RO.md: Premiere real cu V1/A1 goale, V5 liberă/ocupată, readback+vizual+Unicode, snapshot V1/A1/V3/V4, conflict exact două alegeri, update Beta cu SHA-256, backup și rollback; 05 HOLD.
- Regresie ADĂUGATĂ în feature/r20-independent-graphics-gate: experimental/r20/r204/tests/test_r204_properties.py (200 combinații sintetice, indici Bold valizi, text păstrat, liniile <=33, determinism, Unicode); commit a51d5f3aca5cc55941e159784969e6fa58ab6ca1. Testul corespondent a trecut LOCAL pe codul real R2.0.4 + r171_layout din pachetul propriu: 200/200 cazuri, aprox. 12,1s total.
- Un stres inițial 1.200 de cazuri într-un singur proces a depășit limita sesiune; nu reprezintă dovada unui blocaj per carton. Timpii pe exemple individuale realiste observați în teste au fost ~0,001–0,1s; fără benchmark local Premiere/Windows. Nu prezenta acest lucru ca viteză R2.0 certificată.
- R2.0.4 Beta rămâne publicat, sursa executabilă din release NU a fost modificată de acest test aditiv. LIVE pe V5 încă **NEVERIFICAT**. Următoarea intervenție a utilizatorului este indispensabilă doar pentru test Premiere 25.6.4 pe copie/secvență TEST și confirmarea readback/imaginii. Nu cere ZIP manual.


## R2.0.4 — Captură din Premiere LIVE (27 octombrie 2026)
- Utilizatorul a transmis screenshot Premiere la Program Monitor TC `00:00:40:19` cu cartonul vizibil în două rânduri, Unicode corect și evidențiere Orange/Bold funcțională. Timeline arată 8 MOGRT pe V5, alte grafici pe V3/V4, fără montaj pe V1/A1 aparent; V3/V4 au pictogramă eye slash (ascunse la monitorizare).
- Textul vizibil: `UNII ELEVI ÎNVAȚĂ ÎN SISTEM / DUAL: ȘI LA ȘCOALĂ, ȘI LA MUNCĂ`, colorat `ELEVI ÎNVAȚĂ`, `ȘCOALĂ,`. Evaluare: aspect şi două rânduri conforme. Totuși conceptul `SISTEM DUAL` este neaccentuat, deși este cheia mesajului; următorul patch candidat trebuie să prioritizeze expresiile tematice compuse în fața unor cuvinte generice.
- Status: `PREMIERE LIVE VISUAL PARTIAL PASS`; lipsește readback-ul 8/8 cu text și Bold Words, verificarea altor cartoane și testele V5 ocupată/rollback. Captura nu certifică sincronizare audio sau nemodificarea pistelor prin hash.
- Nu face release stable şi nu pretinde 04 complet validat. R2.0.4 Beta publicat, R1.9.13 Stable protejat, VO 05 HOLD.


## R2.0.5 — corecție semantică candidat izolat (NU publicat, 27 octombrie 2026)
- După captura live R2.0.4, branch feature/r20-independent-graphics-gate include experimental/r20/r205/candidate/tools/r204_carton_layout.py: selectarea literală a conceptului de 2 cuvinte dinaintea unui colon explicativ, urmată de termeni tematici după colon. Exemplu vizat: `SISTEM DUAL:` trebuie să aibă prioritate față de `ELEVI ÎNVAȚĂ`, păstrând 2 rânduri, textul intact și indicii Bold 1-based fizic chiar peste line break. Cifra/procentul rămâne prioritară; fără inventarea expresiilor.
- Teste sintetice candidate în experimental/r20/r205/tests/test_r205_semantics.py (inclusiv 200 inputuri random cu seed) și workflow CI separat .github/workflows/r205-semantic-regression.yml în branch. **Nu marca PASS până nu sunt verificate rezultatele CI/locale.**
- R2.0.4 Beta NU a fost suprascris, stable R1.9.13 NU a fost schimbat, nu există release R2.0.5. Testul live vizual R2.0.4 e PARȚIAL; confirmarea reală a celor 8/readback/rollback rămâne deschisă.


## R2.0.4 — READBACK LIVE 8 MOGRT V5 confirmat (27 octombrie 2026)
- Captură utilizator din extensia Premiere: `[PREMIERE READBACK] READBACK PASS: 8 MOGRT pe V5 — EDITORIAL_PREVIEW`, modul 04 `Independent din scenariu`, poziționare `De la începutul pistei (00:00)`. Aceasta CERTIFICĂ numărul 8/8 la readback LIVE, nu și fiecare parametru MOGRT în parte.
- Observație UI din aceeași captură: sub butonul `Generează V5 din DOCX` încă sunt afișate `Verifică rezultatul`, `Generează planul R17 și apasă Verifică.` și copy explicativ legacy (inclusiv referința la pauze R143). Aceasta este confuzie de interfață, nu defect de generare. Soluția corectă este izolarea vizuală a controalelor legacy per mod: ascunse în Independent, restabilite nemodificat în Pe montaj existent; statusul independent READBACK nu se ascunde.
- Înainte de release final: validare 8/8 text/Bold, V5 ocupată, integritate alte piste, rollback, un al doilea DOCX. Se păstrează R1.9.13 stable și 05 HOLD.


## R2.0.5 — UI independent/sincronizat, candidat izolat (2026-10-27)
- După READBACK LIVE PASS 8/8 V5, în captura CEP s-a observat coexistența nejustificată a butonului `Verifică rezultatul` și a instrucțiunilor R17/R143 în modul 04 Independent.
- Nou patch pe branch feature/r20-independent-graphics-gate: `experimental/r20/r205/candidate/cep/r20_panel.js` preia o copie a stilurilor originale ale elementelor legacy la inițializarea fiecărui modul 02/03/04; când Independent, ascunde vizual doar elementele legacy, păstrând butonul de generare R2.0, selectorul de poziție, statusul READBACK și protecția coliziunilor; când Pe montaj existent, restaurează exact stilurile inițiale și onclick-ul stabil. Nu rescrie executoarele ExtendScript, 01/05, planificatorul ori MOGRT-urile.
- Test DOM mock adăugat: `experimental/r20/r205/tests/test_r205_ui.js`, verifică 3 module, tranziție în ambele sensuri, restaurare buton/handler, status și accordions închise. Workflow `.github/workflows/r205-semantic-regression.yml` include `node --check` și mock UI.
- Aceste schimbări sunt **numai în candidate branch**, NU în release R2.0.4; **rezultatele CI pentru UI nu au fost încă obținute**, deci stadiul este `PENDING CI / NOT LIVE`, fără nou Beta instalabil. După confirmarea CI urmează test LIVE UI fără regenerare/dislocare cartoane existente.


### R2.0.5 — rezultate locale confirmate după captura LIVE V5 (27 octombrie 2026)
- **UI candidate LOCAL PASS:** pe copia izolată a sursei CEP s-a executat `node --check` + test mock DOM Node 22: 3 module 02/03/04 comută Independent/Synced, ascund complet instrucțiunile/butoanele legacy doar în Independent, restaurează vizibilitatea și onclick-urile în Synced, mențin statusul R2.0, toate accordions închise; antetul afișează `R2.0 Beta · V3/V4/V5` și restaurează eticheta legacy în Synced. Aceasta **nu este PREMIERE LIVE PASS**. Testul corespondent este comis în experimental/r20/r205/tests/test_r205_ui.js, candidata în experimental/r20/r205/candidate/cep/r20_panel.js.
- **Semantics candidate LOCAL PASS:** exemplul exact din captură a produs `SISTEM DUAL:` ca primă accentuare și `ȘCOALĂ,` ca a doua; layout 2 rânduri `UNII ELEVI ÎNVAȚĂ ÎN SISTEM DUAL:` / `ȘI LA ȘCOALĂ, ȘI LA MUNCĂ`; text neschimbat, `Bold Words` corespunzător (rând 3 pozițiile 5,6; rând 4 poziția 3). Pe codul de lucru cu aceeași regulă au trecut 11 teste layout vechi + 200 cazuri sintetice de integritate (~12s). Teste CI pentru commitul GitHub R2.0.5 încă neconfirmate.
- **Starea release:** NU s-a publicat R2.0.5; R2.0.4 rămâne Beta, R1.9.13 Stable. Pentru următorul test LIVE al modificărilor UI/semantic, nu se modifică secvența de test existentă până la preflight și backup. Nu se declară LIVE pentru patch.


## CHECKPOINT 2026-10-27 — R2.0.5 Beta publicată și teste automate zilnice
- GitHub prerelease `v2.0.5` verificată: https://github.com/Sankio9/ai-video-editor-updates/releases/tag/v2.0.5 ; ZIP 9464 B, SHA-256 `0c2af0a11dea5a2234e840551059d8712da1c4dec1290a22963ca63442561469`. Delta exclusiv `cep/r20_panel.js` și `tools/r204_carton_layout.py`, requires `v2.0.4`, SHA `before_sha256` verificat. `v1.9.13` rămâne Stable.
- Publicarea CI: https://github.com/Sankio9/ai-video-editor-updates/actions/runs/40553121226 — PASS; ultima regresie separată 02/03/04: runs `40553391478`, `40553403216` — PASS. Nu echivalează cu verificare LIVE Adobe Premiere.
- Corecții: 04 highlight literal concept dinainte de colon (`SISTEM DUAL:` în loc de `ELEVI ÎNVAȚĂ`), 2 rânduri maxim 33 caractere, `Bold Words` pe rând fizic; UI 02/03/04 ascunde descrieri/butoane legacy numai în Independent, restaurează sincronizat, afișează `R2.0 Beta V3/V4/V5`. Mock UI în ambele sensuri PASS.
- GitHub Actions DAILY read-only în `.github/workflows/r20-unattended-regression.yml` pe main la 06:15 UTC: Python semantic, mock MOGRT, guard/rollback, NameTag și verificare Stable. Nicio instalare/promoție automată; GitHub Actions nu poate valida Premiere Windows real și nu rescrie cod în mod autonom.
- Încercarea de a crea o automatizare de chat pentru monitorizare condițională a fost respinsă cu `too_many_active_automations` (5/5). Nu s-a dezactivat nicio automatizare existentă fără acordul utilizatorului. Nu promite notificări ChatGPT automate sau codificare continuă peste noapte.
- Rămân NECESARE pentru Stable: Premiere LIVE pe 01 (ASR 8 REVIEW+2 NO_MATCH /9974), 02 independent+sincronizat, 03 independent+sincronizat, 04 Beta R2.0.5 (textul fiecărui cartel, Bold, V5 ocupat, rollback), updater real în două rădăcini CEP; 05 rămâne HOLD. Nu se promovează Stable fără probe P0.


## R2.0.6 — checkpoint ASR Recovery Lab (27 octombrie 2026)
- Pe `feature/r20-independent-graphics-gate`, implementat `experimental/r20/r206/tools/r206_selective_asr.py`: generator local read-only de cereri de retranscriere din `aive-match-diagnostic-v1`, fără a modifica timeline, fără ASR efectiv. Rezultatul `aive-r206-asr-rescan-request-v1` unește cererile per sursă, prioritizează NO_MATCH și WEAK_TRANSCRIPT, pentru WEAK_BOUNDARY folosește ASR candidate ±20 s ori reporter TC numai ca zonă de **căutare**, niciodată tăietură. Fără TC permite întreaga sursă numai <=8 min; peste 8 min și fără ancoră => BLOCKED. Cod sursă contradictoriu, durată contradictorie, CUT duplicat => STOP; match status necunoscut => BLOCKED, nu ignorat.
- Diagnosticul REAL din Library `last_match_diagnostic.json` a fost inspectat **privat**, fără export în repo: 19 fragmente, 7 surse, distribuție `REVIEW_SUGGESTED=9`, `REVIEW_WEAK_BOUNDARY=7`, `REVIEW_WEAK_TRANSCRIPT=1`, `REVIEW_NO_MATCH=2`. Numai cele 10 nesigure sunt prioritizate. Nu declara nou match ACCEPT / nu inventa progres de montaj.
- 18 teste sintetice în `experimental/r20/r206/tests/test_r206_selective_asr.py` + CI run https://github.com/Sankio9/ai-video-editor-updates/actions/runs/40555364392 `SUCCESS`. Include blocarea statusurilor necunoscute și a contradicției codului ASR, plus anonimizarea textelor în output. Workflow izolat `.github/workflows/r206-selective-asr.yml`, adăugat și la regresia automată zilnică `.github/workflows/r20-unattended-regression.yml`.
- IMPORTANT: R2.0.6 **nu este** release instalabil și nu re-transcrie încă audio. Urmează legătura cu motorul faster-whisper existent, selectarea ferestrelor pe GPU, ASR împotriva halucinațiilor (în special ambianță), noua potrivire speech-first și testele LIVE pentru 01. Nu umbla la R1.9.13 Stable sau la R2.0.5 Beta, nici la 05 VO (HOLD).

## R2.0.6 — progres executor local offline (27 octombrie 2026)
- În branch `feature/r20-independent-graphics-gate`, adăugat `experimental/r20/r206/tools/r206_retranscribe.py`. Primește cereri din plannerul `r206_selective_asr.py` + mapări locale ale codurilor media; face preflight complet și verifică durata prin ffprobe, decupează cu FFmpeg în WAV temporar, retranscrie prin model faster-whisper CTranslate2 **local** fără download, oferă absolute word timestamps și avertizări ASR_EMPTY / POSSIBLE_ASR_REPETITION. Fiecare rezultat rămâne `REVIEW_REQUIRED`; `automaticCuttingAllowed:false`; fără operații în Premiere.
- Siguranță: model local `model.bin` obligatoriu, opt-in explicit `--execute`, audio temporar eliminat, fără path-ul media în rezultatul final; orice sursă offline/invalidă sau durată schimbată => STOP, fără execuție ASR. Rezultate transcrise PRIVATE local, nu GitHub. 05 VO HOLD.
- CI `40556352429` SUCCESS: 18 teste planner + 12 teste executor mock = **30 tests PASS**; ffmpeg, CUDA, real media și modelul efectiv nu au fost rulate în CI, deci NU reprezintă `LIVE PASS` și nu dovedesc calitatea potrivirilor.
- Urmează integrarea `r206_retranscribe` în motorul deja validat 01, reutilizarea cache și măsurători pe RTX 3070 fără manual CMD. R2.0.6 rămâne doar laborator; R1.9.13 Stable și R2.0.5 Beta sunt neschimbate.
