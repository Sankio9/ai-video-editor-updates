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
