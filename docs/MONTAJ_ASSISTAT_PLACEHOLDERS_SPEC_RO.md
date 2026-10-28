# AI Video Editor — Montaj inteligent cu recuperare și spații rezervate (propunere R2.2, 28.10.2026)

**Statut:** SPECIFICAȚIE PROPUSĂ, NU IMPLEMENTARE LIVE. De implementat în Beta separată de R2.1.3, cu aprobarea utilizatorului din panou **înainte** de modificarea timeline-ului. Un singur buton existent `Montează după scenariu`; analiza, decizia și cazul incomplet se gestionează automat, fără moduri separate. Stable R1.9.13 este protejat. Fără schimbări în 02/03/04/05.

## Problema reală observată în Bubuieci

Diagnosticul local furnizat de utilizator (NU publica fișierul privat, textele, numele sau media în GitHub public) conține **19 CUT-uri**: **9 `AI_MATCHED`**, **7 `REVIEW_WEAK_BOUNDARY`**, **1 `REVIEW_WEAK_TRANSCRIPT`**, **2 `REVIEW_NO_MATCH`**. Captura interfeței indică `OPRIT: 10/19`. Cele 10 CUT-uri nesigure sunt 01,02,04,05,06,07,08,17,18,19. Sursa 9974 (18–19) nu are nicio potrivire ASR; intervalele sale `finalIn/finalOut` sunt fallback de reporter, NU dovezi audio. CUT-04 are `scriptIn=131`, `scriptOut=132`, dar fereastra ASR aproximativă are peste 5 secunde; nu folosi 1 sec ca durată finală fără verificare. CUT-08 e `timecodeHint` / script range 0–20.605 și fereastră ASR slabă 85–106.72; nu insera automat de la 0. Aceste valori sunt în diagnostic local, nu se copiază în testele publice.

## Flux unic de montaj — decizie explicită confirmată de utilizator

**Nu există două butoane, două moduri ori selector Complet/Asistat.** Unicul buton `Montează după scenariu` lansează întotdeauna o analiză completă (DOCX, scanare recursivă Project Panel, cache ASR, potrivire, plan secvență) **fără a modifica timeline-ul**. Se analizează toate blocurile (sincronuri, spații VO, separatoare), după care:

- **0 probleme:** preflight de integritate + coliziuni, apoi inserare completă fără dialog suplimentar. Rezultat `MONTAJ COMPLET` doar dacă readback-ul confirmă tot.
- **1+ CUT-uri nesigure/negăsite:** afișează rezumatul (confirmate / rezervate / motive / durate estimate); **unicul** dialog cere `Continuă cu spații rezervate` sau `Oprește`. Nicio inserare parțială fără această aprobare explicită.
- **Piste ocupate, proiect schimbat, surse duplicate/contradictorii, motor/plan invalid:** STOP de siguranță fără opțiune distructivă; problemele de validitate pot deveni placeholder numai dacă au fost analizate, nu cauzează coliziuni și riscul este comunicat.

## Pașii de execuție

1. **Preflight + rezumat exact**: `19 evenimente / 9 audio confirmate / 10 rezervate / coduri negăsite / estimare durată`; fiecărei probleme îi indică motivul (lipsă sursă, audio negăsit, TC incomplet, timecode imposibil, sursă offline, conflict etc). Sursele ambigue sau duplicate sunt blocate pentru auto-insert.
2. **Aprobare explicită numai când există probleme** `Continuă cu montajul parțial și spații rezervate` sau `Oprește, nu modifica timeline-ul`. Fără bifă/alegere sau dacă analiză se schimbă, STOP. Nu ascunde numărul de CUT-uri lipsă.
3. **Execuție sigură**: doar pe **copie nouă de secvență** sau secvență de test confirmată goală V1/A1; proiect original, alte track-uri și clipuri user intacte. Preservă ordinea DOCX, VO-card gaps și toate pozițiile din plan. Pentru `AI_MATCHED` (cu IN/OUT audio validat) inserează sursa corectă cu sunet; pentru orice REVIEW/NO_MATCH lasă un slot de aceeași lungime estimată pe V1/A1, fără video/audio deghizat în real. NU folosi TC reporter pentru a crea `finalIn/finalOut` de clip.
4. **Placeholder propus**: **slot gol pe V1/A1** + **marker de interval pe SEQUENCE** (codul CUT, sursa cerută, motiv, `DURATA ESTIMATĂ`). Opțional, dacă V2 e deja liberă și preflight o confirmă, un singur card/slate simplu 16:9/9:16 `CUT-XX / SOURCE-XXXX / AUDIO NECONFIRMAT` pe V2 pentru vizibilitate. Nu crea automat track V2; nu insera un Color Matte/Adjustment Layer pe pista cu sursă fără test Adobe Premiere LIVE. Niciodată un `adjustment layer` ca placeholder implicit: este transparent și aplică efecte dedesubt. O imagine/slate locală ar fi doar pe o pistă separată validată.
5. **Estimare durată a slotului**: folosește *numai pentru TIMELINE spacing*, nu pentru alegerea source IN/OUT. Dacă `rawMatchedIn/Out` există dar scorul e slab, diferența ASR este un indicator aproximativ, fără eticheta `MATCHED`. Dacă nu există, estimare din număr cuvinte al replicii, rate speech parametrizabil și timp VO/respirație; reporter TC poate fi un indiciu comparat cu estimele numai dacă plauzibil. Eticheta obligatorie `ESTIMAT` + formula/proveniență; utilizatorul poate ajusta numeric înainte de insert. Nu stabili automat 1sec pentru o replică de 5–7sec.
6. **Identitate pe termen lung**: plan JSON versionat și hash: `docx_sha256`, id secvență, id grup/cut, cod sursă, status `CONFIRMED / PLACEHOLDER / BLOCKED`, timelineStart/End, sourceIn/Out DOAR CONFIRMED, reason, estimateMethod, priorSourceFingerprint, status de aprobare și provenance. După inserare verifică numărul/durata/materialele efective; salvează în Temp local numai. Nu publica în GitHub texte private.
7. **Înlocuire ulterioară**: acțiune separată `Rezolvă CUT-XX`, cu preflight ASR/sursă/manual IN/OUT, doar dacă slotul este încă același (id/hash/durată/inventar) și noul clip încape, fără ripple și fără mutarea clipurilor validate. Dacă lungimea diferă, cere `Retiming` explicit (sau stop) în loc de deplasări automate.
8. **Siguranță**: succes parțial = `DRAFT / NECESITĂ REVIZIE`, niciodată `Montaj complet`. Oprire pe pista ocupată/locked, coliziune, offline, intervenția userului în timpul executării, sequenceID schimbat ori readback incorect. Backup, rollback numai pentru obiectele inserate de agent, niciodată de clipuri ale editorului. Fără QE API.

## De ce NU Color Matte sau Adjustment Layer ca prima opțiune

- Markerele de secvență și intervalele lor sunt disponibile prin Premiere ExtendScript; nu afectează imaginea/video/audio și sunt potrivite pentru corecții editoriale.
- `Track.insertClip` (insert edit) poate avea efecte de rearanjare/ripple; `Track.overwriteClip` distruge conținutul existent. Niciuna nu se folosește înainte de inventar de piste + o copie de secvență + verificare fără coliziuni. Pentru montage sloturi, folosește poziții absolute pe pistă goală, nu inserări cu ripple.
- Adjustment layers modifică efectele de sub ele când au efecte; un blank color matte ascunde materialele inferioare și poate ajunge accidental în export. Slate opțional se pune numai V2 liberă și nu substituie markerul.
- Pentru R2.2, prima versiune LIVE poate livra doar `V1/A1 gol + markere`; slate-ul opțional trece într-un al doilea test de compatibilitate.

## Acceptance P0

- Synthetic fixture 19 total, 9 confirmed, 10 placeholder, **zero** fallback TC inserts.
- Media absentă / TC invalid / speaker repeated / ASR missing: toate produc slot, nu clip presupus.
- CUT-uri păstrate în ordinea DOCX și începuturile celorlalte CUT-uri invariabile când slotul se umple fără ripple.
- Preflight neinvaziv. La 0 probleme, montaj complet fără dialog. La 1+ probleme, aprobarea utilizatorului pentru sloturi este necesară și verificată chiar înainte de primul insert. Un singur buton principal în 01.
- Timeline existent cu user clips: STOP, niciun update.
- După insertion, readback exact număr de clipuri validate, sloturi rezervate și markere; rollback dacă mismatched.
- Independent 02/03/04 rămân funcționale, A2 VO HOLD; nu se adaugă automat MOGRT pe V5 și nu se creează piste prin QE.
- LIVE Premiere 2025 v25.6.4 pe copia Bubuieci: 9 confirmate + 10 sloturi marcate, durate estimate vizibile și editabile; verificare export fără slate accidental. Doar după acest test se poate considera Beta utilizabilă.

## Roadmap

P0: parser diagnostic + planul `CONFIRMED/PLACEHOLDER`, estimări + UI rezumat/alegere.
P1: writer pe copie secvență V1/A1 + sequence markers, readback, rollback.
P2: action `Rezolvă CUT`, re-ASR selectiv R2.0.6, fixarea slotului fără ripple.
P3: comparație cu editările editorului pentru „Învață din corecturile mele”, numai după aprobare.


## R2.2 — notificare obligatorie despre fișiere și CUT-uri neintroduse (cerință utilizator, 28.10.2026)

**Regulă P0: nu lăsa editorul să caute singur ce lipsește.** R2.2 păstrează **un singur** buton principal `Montează după scenariu`. În urma analizei, dacă există măcar un CUT care nu poate fi inserat sigur, afișează obligatoriu un raport contextual **înainte** de alegerea `Continuă cu spații rezervate` / `Oprește`; după montajul parțial afișează o notificare persistentă în **01 Montaj**, până când lipsurile sunt rezolvate sau editorul închide explicit raportul. Nu ascunde erorile în consola tehnică și nu deschide câte o fereastră pop-up pentru fiecare CUT.

### Ce trebuie să vadă editorul

**Rezumat:** `Montaj parțial — 9/19 sincronuri inserate, 10 spații rezervate. Verifică materialele marcate.` Aceste numere sunt doar un EXEMPLU de fixture Bubuieci, nu valori hardcodate. Distinge între `ANALIZĂ` (înainte de scriere) și `REZULTAT CONFIRMAT` (doar după Premiere readback real). Nu declara `inserat` înainte de readback.

**Listă extensibilă „Materiale care necesită intervenția ta”**, în ordinea DOCX; fiecare rând conține:
- `CUT-ID` + **cod sursă 4 cifre** + numele real al fișierului dacă a fost detectat în Project Panel (altfel `Fișier negăsit în Project Panel`), fără a inventa nume;
- **motiv distinct**, unul dintre `SOURCE_NOT_FOUND`, `SOURCE_OFFLINE`, `SOURCE_AMBIGUOUS`, `AUDIO_NOT_FOUND`, `ASR_WEAK_BOUNDARY`, `ASR_WEAK_TRANSCRIPT`, `TC_INCOMPLETE_OR_IMPLAUSIBLE`, `OTHER_REVIEW`, `INSERTION_FAILED`. Nu prezenta `AUDIO_NOT_FOUND` drept `FILE_MISSING`; fișierul poate exista dar sincronul să nu fie identificabil în audio;
- **acțiunea necesară**, explicată simplu (reconectează media / verifică declarația manual / verifică timecode / alege sursa corectă / reîncearcă ASR);
- poziția `timelineStart` și intervalul estimat rezervat, afișate ca timp Premiere după ce planul este validat; **durată estimată** trebuie etichetată explicit. Pre-insert poate avea doar timp planificat, nu timp verificat;
- starea `REZERVAT`, `REZOLVAT` sau `BLOCAT`, actualizată doar după readback/diagnostic valid. Dacă un fișier alimentează mai multe CUT-uri, arată **fiecare CUT separat** și numărul total de fișiere distincte negăsite, pentru a evita confuzia „10 CUT-uri = 10 fișiere”.

**După montaj**, în panou o notificare vizibilă, dar neintruzivă: `Montaj parțial finalizat. Au rămas N sincronuri de verificat — Vezi lista`. Lista se poate deschide oricând după operație; conține link de navigare la **markerul de secvență** pe fiecare rând **numai dacă Premiere API permite saltul sigur** (altfel afișează timecode-ul și marker name pentru navigare manuală). Nu adăuga un alt buton principal pentru montaj.

**Raport local permanent**: `D:\AI-Video-Editor\Temp\Montage\<sequence-id>\missing_sources_report.json` (sau un nume stabil similar), cu identitate seq, DOCX SHA, plan SHA, cod/cut/motiv, nume sursă numai local, durate estimate + metoda estimării, poziție marker, status și timestamps. Scriere atomică, zero upload public, fără transcrieri în raportul de notificare. La repornirea panoului, dacă identitatea secvenței și a planului coincid, recuperare read-only a raportului; dacă nu, afișează `raportul nu mai corespunde secvenței active`, nu reaplica automat nimic.

**Rezolvare în timp**: la validarea/reinserarea unui CUT, marchează `REZOLVAT` numai după Premiere readback. Scade contorul și păstrează istoric; nu șterge slotul ori markerul automat dacă inserarea a eșuat. Permite `Copiază lista` sau `Exportă raport` doar ca acțiune secundară în lista deschisă, nu în bara principală 01.

### Tests P0

- [ ] La 0 CUT-uri nesigure, montaj complet fără dialog/avertizare inutilă; final `19/19` doar după readback.
- [ ] La 10/19 incerte, dialogul arată **toate cele 10 CUT-uri**, codurile, motivul și estimarea, înainte de aprobare; după readback arată numărul real inserat și rezervat.
- [ ] CUT-18 și CUT-19 cu aceeași sursă 9974 apar ca **două CUT-uri** cu **un singur fișier distinct** (dacă acesta există); statutul este `AUDIO_NOT_FOUND`, nu `SOURCE_NOT_FOUND`, când fișierul e online dar vorbirea nu e recunoscută.
- [ ] Media absentă/offline/duplicată nu duce la scriere nesigură; raportul distinge exact condiția.
- [ ] Listă persistentă după reîncărcarea panelului pentru aceeași secvență; nu se amestecă rapoarte ale secvențelor diferite.
- [ ] Refuz `Oprește` => zero inserări și zero raport fals de `montaj finalizat`; planul/diagnosticul local poate rămâne read-only.
- [ ] Nicio valoare privată exportată în GitHub sau telemetrie; fără transcrieri/mesaje sensibile în notificări.


## R2.2 — implementare inițială planificator (CI) — 28.10.2026

- **Cod candidat existent**, nu doar specificație: `experimental/r20/r220/tools/r220_montage_plan.py`, GitHub branch `feature/r20-independent-graphics-gate`. Folosește diagnostic curent `aive-match-diagnostic-v1`, context SHA256 (DOCX+diagnostic), identitatea secvenței, inventar Project Panel și lista de CUT-uri care au trecut **validatorul de siguranță moștenit**. Eticheta `AI_MATCHED` singură NU autorizează inserarea.
- Rezultat **ANALYSIS_ONLY**: `CONFIRMED` pentru audio verificat cu `sourceIn/sourceOut`, `PLACEHOLDER` pentru orice CUT nesigur, cu `timelineStart/End`, durată ESTIMATĂ numai din ASR slab plauzibil sau word-count, motiv exact și action. Niciun fallback la reporter TC pentru source IN/OUT. Media ambiguă/necunoscută și statusul necunoscut blochează planul.
- `decide(...)` solicită `CONTINUE_WITH_PLACEHOLDERS` când există probleme; `STOP` nu autorizează scrierea. Chiar după aprobare returnează `PENDING_LIVE_PREFLIGHT` și `writeAuthorized:false`; scrierea efectivă pe V1/A1 nu este implementată.
- `verify_readback(...)` poate construi raportul `POST_READBACK` numai din lista exactă de clipuri și markere returnate de viitorul writer Premiere; rezultatele nu sunt inventate la finalizarea analizei. Raportul este atomic și local, fără textul interviului.
- **CI PASS** https://github.com/Sankio9/ai-video-editor-updates/actions/runs/40726539952 — 19 teste noi sintetice + regresii din matcher R2.1.3 și planificarea ASR R2.0.8. Acest rezultat **nu este Premiere LIVE PASS**. Nu modifica release/next.json / v1.9.13 Stable.
- **P0 următor:** adaptarea motorului 01 pentru un singur buton, scanarea întregului DOCX, preflight fără scriere, dialog contextual (numai la CUT-uri nesigure), apoi writer atomic pe copie de secvență V1/A1 + markere, readback/rollback și raport persistent în panou. Nu publica Beta ca funcțională fără test LIVE Premiere.


## IMPLEMENTARE CANDIDAT R2.2 — writer V1/A1 și markere (CI, 28.10.2026)

- Implementat ExtendScript **experimental**, `experimental/r20/r220/cep/jsx/r220_montage_writer.jsx` pe branch `feature/r20-independent-graphics-gate`. Are `preflight(plan,choice)` și `commit(plan,choice,approvedPlanSHA)`; nu este încă încărcat/invocat din butonul 01. NU ESTE release instalabil și NU ESTE LIVE PASS.
- **Preflight**: protejează identitatea secvenței, necesită copie explicită cu `[AIVE TEST]` în nume, V1/A1 existente, goale și unlocked, markere AIVE-R220 inexistente, codurile CUT, statusuri, surse cu nodeId verificat în Project Panel, nume real și media online, intervale validate numeric. Niciun `QE`, niciun track nou. Reporter TC nu devine source IN/OUT.
- **Writer**: folosește numai `Sequence.overwriteClip` pe pistele V1/A1 **goale**, cu exact sourceIn/out pentru CONFIRMED; restaurează source ProjectItem In/Out; lasă V1/A1 libere la PLACEHOLDER și creează markere de interval `AIVE-R220 CUT-xx code` cu motiv și durată estimată. Verifică clipurile și markerul după fiecare inserare și numărul complet la final; orice eșec încercă rollback numai pentru obiectele create (TrackItem.remove cu `ripple=false`, MarkerCollection.deleteMarker). Nu promite rollback perfect înainte de test în Premiere.
- `experimental/r20/r220/tests/test_r220_writer.js` simulează Premiere în Node: 8 scenarii inclusiv `preflight` fără scriere, `copy required`, V1 ocupată STOP, sequenceID greșit, media greșită, placeholder fără source IN/OUT, inserare eșuată + rollback și protecția contra rerulării. Referințe API inspectate: https://ppro-scripting.docsforadobe.dev/sequence/sequence/ ; https://ppro-scripting.docsforadobe.dev/collection/markercollection/ ; https://ppro-scripting.docsforadobe.dev/item/trackitem/ .
- Planificatorul `r220_montage_plan.py` actualizat cu media `nodeId` validat, compatibilitate cu diagnosticul real R1.9.13 `asr.status` + `scriptText` (față de prototipul vechi `matchStatus` + `text`), statusuri contradictorii STOP. CI `40728601602` **SUCCESS** cu 21 teste de plan, 8 scenarii mock writer, 18 ASR și 2 8/17 regression tests.
- Auditul codului public `cep/r193_workflow.js` R1.9.10, 154 linii: modul 01 are `cutR193Start`, `runWorker`, `buildLegacy`; la eroare `run()` doar afișează `OPRIT`, fără fallback. **P0**: integrare planificator R220 în acea ramură de eroare, cu context hash, scanare reală Project Panel, revalidarea whitelist AI_MATCHED, dialog contextual de aprobare, încărcare JSX pe copia de secvență, raport persistent și verificare VO cards/gaps din DOCX înainte de inserare.
- ATENȚIE: `last_match_diagnostic.json` R1.9.13 poate avea numai CUT-uri, fără toate cardurile VO/spațiile editoriale. **Nu construi automat timeline final doar din acest JSON** până nu există mapare completă a ordinii DOCX. Niciun update Beta/Stable până la integrare și test LIVE pe copia Bubuieci.
