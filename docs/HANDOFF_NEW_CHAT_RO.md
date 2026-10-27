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
