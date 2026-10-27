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
