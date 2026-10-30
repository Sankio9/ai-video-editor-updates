# AI VIDEO EDITOR — MASTER SPEC & DECISIONS (RO)
**Revizie:** 2026-10-27 · **Statut:** normativ pentru continuarea proiectului · **Repo distribuție:** `Sankio9/ai-video-editor-updates`

> Acest fișier este sursa de adevăr pentru cerințele utilizatorului și evoluția aprobată. Nu echivalează cu certificarea funcțională a vreunei versiuni. La fiecare sesiune nouă, citiți împreună `docs/ACCEPTANCE_TESTS_RO.md` și `docs/HANDOFF_NEW_CHAT_RO.md`. Nu publicați cod sursă editorial privat, DOCX-uri, audio/video, transcrieri sau date din proiecte în repository-ul PUBLIC.

## 1. Obiectiv permanent
Extensie AI Video Editor — Reportaj pentru **Adobe Premiere Pro 2025 25.6.4/Windows**, instalare locală `D:\AI-Video-Editor`. Un **singur DOCX** ales în modulul **00**, surse video/audio importate oriunde în **Project Panel**, categorii cu **câte UN singur buton** fiecare: **01 Montaj**, **02 Subtitrări MOGRT**, **03 NameTag**, **04 Cartoane**, **05 VO (HOLD)**. Fără lansări CMD, fără pregătirea manuală a fișierelor JSON, fără dialoguri inutile și fără transfer între alte programe. Schimbarea DOCX-ului trebuie să invalideze orice rezultat incompatibil; fiecare proiect/reportaj are namespace propriu.

**REGULĂ NOUĂ EXPLICITĂ:** 02, 03, 04 trebuie să poată fi folosite **independent de 01**. Utilizatorul poate alege DOAR Cartoane, DOAR NameTag sau DOAR Subtitrări și să creeze elementele direct pe timeline, chiar dacă V1/A1 nu are montaj. Nu este admis să ruleze/cerem planul complet R143 drept condiție obligatorie a acestor moduri. Trebuie menținut și modul pe montaj existent cu sincronizare exactă.

## 2. Două moduri de poziționare, fără confuzie
**A. SINCRONIZAT CU MONTAJUL:** când V1/A1 deja corespunde montajului validat, 02/03/04 ancorează grafica în tăieturile reale, după verificarea planului și secvenței; NU o deplasează arbitrar. Păstrează comportamentul modulelor stabile.

**B. INDEPENDENT DIN SCENARIU:** când nu există montaj R143 / nu se dorește acesta, modulul solicitat creează **o bandă de prezentare grafică** în ordinea editorială din DOCX. Pentru NameTag: un MOGRT per bloc editorial de identificare (nume+funcție), nu per replică. Pentru Cartoane: numai blocurile VO/caption din Word, despărțite prin pauze scurte între blocuri/pagini, nu golurile rezervate montajului. Pentru Subtitrări: doar textul replicilor din Word în grupuri separate pe V3; **fără audio prezent în secvență, sincronismul cu vocea NU poate fi pretins** — se folosește timing de lectură marcat vizibil `SCRIPT_PREVIEW` până la ancorarea ulterioară la audio. Nicio sintetizare falsă de timecode audio. Totul se poate crea într-o secvență goală, pe pistele existente, fără a atinge V1/A1. Opțiune de separator configurabilă în secunde (propunere inițială 0.75 s, nu regulă editorială definitivă). Poziționare: la 0 sau după ultimul element de pe pista vizată, în funcție de alegerea explicită. Nu suprascrie conținut existent implicit.

Categoriile trebuie să aibă selector de mod inteligibil; **nu se schimbă automat modul după ce utilizatorul a confirmat**. Rezultatul poate fi `PREVIEW TIMING` sau `SYNCED`; niciodată «sincronizat» pentru timing estimat.

## 3. Reguli montaj (01), obligatorii
1. DOCX determină *ce* trebuie găsit și ordinea editorială; **transcrierea și analiza audio determină IN/OUT real**, nu timecode-ul reporterului.
2. Timecode-ul reporterului este orientativ și poate devia cu ±30–60 s sau mai mult. Căutare extinsă până la ±90 s; acceptarea abaterii rămâne dependentă de scoruri și dovezi, nu doar de distanță. Nu utiliza niciodată fallback automat la TC brut.
3. Pentru **fără TC**: dacă sursa are cel mult **8 minute** se permite transcrierea/căutarea întregii surse; peste 8 min se solicită reper, nu se inventează interval.
4. **Doar IN** / **doar OUT**: estimează durata din cantitatea de text (valoare de pornire ~2.15 cuvinte/s + marjă), extinde fereastra și găsește limitele tot din ASR. Estimarea nu devine tăietură finală.
5. Dacă textul DOCX este parafrazat față de interviu, compară fragmente, răspunsuri și fraze complete. Dacă fraza apare în mai multe locuri, este ambiguă — nu alege orbește pe baza TC.
6. Fiecare sincron nesigur sau absent -> raport `REVIEW`; **nu modifica timeline-ul până la preflight sigur sau până la o alegere editorială explicită**. Nu marca `OK` un montaj cu fragmente omise.
7. Detectează ASR defect/halucinații, limbă greșită, ambianță cu vorbire slabă și transcrieri foarte rare; reanalizează selectiv, nu reduce arbitrar pragurile.
8. Transcrie o sursă o singură dată când există cache valid; nu retranscrie la pornirea Premiere.

## 4. Project Panel și DOCX
- Scannerul parcurge **recursiv** toate `bins`; nu presupune fișiere la rădăcină.
- Potrivește codul de 4 cifre în numele real de pe disc SAU numele din Premiere, inclusiv formatele `CAM_9981_x.mov`. Nu confunda fragmente de numere mai mari; coduri contradictorii/duplicate/offline -> STOP.
- La surse lipsă, afișează **codurile și numele cu ROȘU**, plus lista numelor și a folderelor detectate. Nu presupune automat că greșeala este în media, poate fi în Word.
- DOCX poate avea antet SINCRON/AMB, nume/funcție, cod, TC și text în același paragraf (line breaks). Recunoaște cartoanele all-caps. Nu cere reformatarea Word-ului; nu altera textul editorial fără aprobare.
- UTF-8 obligatoriu pe Windows pentru diacritice românești, JSON și mesajele din proces.

## 5. Subtitrări / NameTag / Cartoane
- **02 V3**: MOGRT approved; text **exact din DOCX** (nu rescris după ASR), reporter Italic doar cu dovezi editoriale, cue timings prin spoken anchors în modul SYNCED. În modul INDEPENDENT, numai preview/timing de lectură dacă nu există audio/ancoră.
- **03 V4**: o burtieră per bloc editorial nume/funcție; gruparea NU deduplică global același vorbitor reintrodus; fără nume/rol -> explicit SKIP/REVIEW; template `RFERL_NameTag_2LinesTitle.mogrt`.
- **04 V5**: cartoane MOGRT `RFERL_Captions_STROKE_2_.mogrt`, text original, reguli maximum 4 rânduri x 33 caractere, accent Orange/Bold, 1..N pagini semantic separate, fără coliziuni; în INDEPENDENT nu rezervă pauze VO/montaj, doar separatoare vizuale. **La „Verifică”, scanează ORICE material pe V5**, chiar dacă este foto, video, MOGRT, alte clipuri, indiferent unde e pe pistă; raport tip+nume+interval. Oferă EXACT două alegeri când V5 este ocupată: (1) «Suprascrie materialele de pe V5» cu acceptare **explicită a riscului distructiv**; (2) «Oprește, eliberez V5». Nicio suprascriere automată. Nu crea piste prin QE API; în trecut QE a deplasat NameTag.
- **05 VO:** HOLD explicit. Nu activa fără acord. Cerințe viitoare documentate: selectare fișier audio -> «Montează VO» pe A2, tăiere după vorbirea reală, deplasare sincronizată a blocurilor următoare, actualizare V5 fără afectarea proiectului original, rollback obligatoriu. Testul izolat de inserare A2 a reușit, sincronizarea globală NU este validată.

## 6. UI și experiență
- Toate `rows`/accordions închise implicit la deschiderea extensiei (inclusiv 00); deschiderea unuia nu trebuie să provoace deschiderea/închiderea involuntară a altuia.
- Bară **Processing** vizibilă global în timpul operațiilor, inclusiv când modulul este pliat. Preferăm progres real surse N/M, cu stare curentă; nu prezenta procente inventate.
- Nicio procesare automată la simpla pornire Premiere. La alegerea explicită a unui DOCX nou, pregătirea poate porni numai potrivit setării/autorizării utilizatorului și trebuie să verifice mai întâi cache.
- Cache persistent, segregat după DOCX SHA, coduri/mărime/mtime/hash sursă, model ASR + configurare + versiune matcher, plan și secvență. Modificarea sau ștergerea transcrierii trebuie să invalideze planurile dependente.
- Politici cache: permanent (implicit), 7/30/90 zile, ștergere imediată pe sursă/reportaj cu confirmare. Nu șterge video, audio sau modele AI. Nu reutiliza rezultatele altui reportaj sau planuri incomplete.
- Viteză: țintă `<60 s` de la «Montează» numai pentru reportaj pre-analizat; raport separat al timpului de transcriere inițială. Optimizați CUDA RTX 3070, warm process/model, `faster-whisper batched` și VAD doar după benchmarking română (calitate + timpi), cu CPU fallback sigur. Nu pretindeți că benchmark extern = rezultat local.
- Fără ferestre de consolă, fără editarea setărilor tehnice/paths sau pornirea altor programe.

## 7. Siguranță și distribuție
- Module existente confirmate nu trebuie destabilizate. Orice mod nou este **gated** explicit (sincronizat vs independent). Nu șterge/suprascrie materiale din timeline pe care nu le deții.
- Import MOGRT numai pe pista stabilită: V3 subtitrări, V4 NameTag, V5 cartoane; V1/A1 sursă, A2 VO când se reia. Nu crea piste prin QE. Pistele lipsă se cer create în Premiere prin UI.
- Verificare înainte de execuție + token revalidat la inserare + readback după fiecare MOGRT. Detectează clipe ocupate, piste blocate, duplicate, material altui proiect și schimbări între verificare și inserare.
- Versiuni prin GitHub Releases + updater CEP, validare allowlist și SHA-256 al fișierelor, exact `before_sha256`, backup automat, rollback testat în două rădăcini CEP. Nu livra ZIP de instalat manual decât diagnostic/prototip explicit.
- Verificarea locală/mock nu este certificare în Adobe Premiere. Primele teste reale doar pe secvență de probă și copii ale proiectelor.
- Nu promite «final / READY» fără toate testele reale și criteriile de acceptare. Rapoarte cu `LOCAL PASS`, `LIVE PASS`, `BLOCKED` separat.

## 8. Dovezi din testul reportajului 2026-10-27 (date anonimizate)
- DOCX editorial cu **19** pasaje și **8** blocuri de cartoane; 7 coduri media.
- R1.9.3 a montat 17 clipuri, dar **8 erau timecode-fallback** (nesigure); decizia: fără fallback automat.
- R1.9.11 a blocat corect timeline-ul dacă 8/17 nepotrivite.
- R1.9.13 a identificat **9 ACCEPT, 8 candidat pentru revizie, 2 NO_MATCH**. Diagnosticul și 6 transcrieri ASR au confirmat parafrazări și ASR de ambianță cu halucinații. NU păstrați transcrieri și textul real în repo-ul public.
- Release GitHub `v1.9.13` era ultima versiune stabilă verificată la data acestei revizii; R1.9.14 este **ASR Audit Lab** (diagnostic, nu release stabil); R1.9.4–1.9.7 sunt candidați parțial separați, NU presupuneți automat instalarea lor.
- Bug-uri remediate în release-uri ulterioare: Windows cp1252 (1.9.8), Project bins + nume sursă (1.9.9), roșu surse lipsă (1.9.10), Speech-first (1.9.11), TC opțional pregătit în 1.9.12 și integrat în 1.9.13.
- Auditați fiecare defect/patch înainte de a afirma că o combinație de versiuni e instalată.

## 9. Ce NU este încă verificat și trebuie făcut
1. Recuperarea celor 8+2 declarații pe transcript-uri românești reale, fără auto-match fals și cu recuperare ASR selectivă pentru ambianță.
2. Mod independent 02/03/04 **EXECUTAT ÎN PREMIERE**, fără niciun montaj pe V1, în secvență goală și pe secvență ocupată.
3. Coexistența vizuală 02–04 și a separatoarelor scurte, verificare V5/destructive choice.
4. Măsurători locale pe RTX 3070 și progres adevărat, cache/purge.
5. Update multi-hop sigur din versiunea instalată cu backup și rollback.
6. Cross-reportage DOCX swap și proiect nou; lipsă/duplicat/offline media.
7. Export diagnostic fără date private în repository.

## 10. Principiu de dezvoltare pentru orice chat nou
**Mai întâi citește acest document, verifică release-ul REAL și sursele locale relevante, apoi modifică doar punctul necesar.** Dacă lipsesc fișiere/capabilități, declară clar, nu presupune. Nu bloca independent grafica pentru o problemă de ASR la montaj.


## Regula actualizată — NameTag independent și blocuri AMB (2026-10-27)
În 03 Independent, un antet editorial `AMB` pentru replici de ambianță fără nume/funcție **nu trebuie tratat drept NameTag lipsă care blochează întreaga generare**. Se identifică antetul AMB și sursa din DOCX; doar cu potrivire explicită se notează `SKIP_AMBIENCE`, vizibil, cu CUT/paragraf/cod, fără MOGRT pentru ambianță. Pentru `SINCRON` sau antet ambiguu cu persoană neidentificată se notează `REVIEW_MISSING_IDENTITY`: consimțământ editorial explicit pentru omitere înainte de scrierea pe V4 (altfel STOP); NIMIC inventat. Cod sursă contradictoriu => STOP. Celelalte NameTag-uri valide pot fi generate pe V4, fără V1/A1, iar V3 rămâne neatinsă. Exemplu local: 8 identificări/2 fragmente ambianță, testele sintetice au trecut, validarea LIVE în Premiere rămâne obligatorie.


## REGULĂ OBLIGATORIE — 04 Cartoane: layout compact și accent editorial (R2.0.4, 2026-10-27)
1. **Textul DOCX este imuabil editorial**: nu parafraza, nu inventa cifre/termeni, nu elimina cuvinte și nu modifica diacriticele. Algoritmul de layout poate schimba numai delimitările vizuale de rând/pagină, cu reconstruirea integrală verificabilă a textului.
2. **Fiecare pagină MOGRT folosește numărul minim fezabil de rânduri** pentru textul ei, fără despărțiri inutile: text scurt într-un singur rând dacă încape; dacă nu, 2/3/4 rânduri, până la maxim **4 rânduri × 33 caractere** per rând. Pauzele de punctuație, lizibilitatea și expresiile semantic legate sunt preferate la departajări.
3. **Accente Orange/Bold pentru informația semnificativă**: cifre, procente, unități și termeni/fraze-cheie extrase din textul original, cu dozaj rezonabil. Nicio accentuare bazată pe date fabricate. Propunerile automate rămân **revizuibile editorial**, nu sunt adevăr semantic garantat. Indicii `Bold Words` trebuie calculați exact pentru rândul MOGRT fizic, 1-based, fără a evidenția un alt cuvânt după reîmpachetare.
4. În **Independent din scenariu**, cartonul pornește exclusiv din blocurile editoriale VO/caption, nu cere 01 montaj, nu rezervă spațiile de montaj sau sincronuri și folosește separatoare scurte între blocuri; preview-ul nu se prezintă ca audio-sync. Pagini multiple ale aceluiași bloc se păstrează separat, în ordine.
5. **Siguranță V5 neschimbată**: inventar complet (orice media/MOGRT, oriunde pe pistă), exact cele două alegeri deja aprobate pentru pista ocupată, acceptare expresă pentru distrugere, fără ștergere implicită, fără QE addTracks. O implementare care nu poate garanta overwrite+rollback se oprește conservator, nu șterge.
6. **Regresie interzisă:** nu modifica 01 Montaj, 02 Subtitrări, 03 NameTag sau 05 Voice-over într-un patch de aspect 04. În particular, păstrează corecția 03/R2.0.3 `SKIP_AMBIENCE` vs `REVIEW_MISSING_IDENTITY`.
7. **Distribuție**: R2.0.4 este prerelease **Beta**, delta SHA-256 cu exact 2 fișiere, instalabilă numai peste versiunea compatibilă R2.0.3 prin updaterul în Premiere; stable rămâne R1.9.13 până la validări LIVE. Fără instalare ZIP manuală. Nici CI/mock, nici readback din teste simulate nu sunt certificare LIVE.


## REGULĂ DE CALITATE — selecție semantică în Cartoane 04 (observație LIVE 2026-10-27)
- Preferă evidențierea **ideii principale/expresiei-cheie compuse** din propoziție față de accentuarea unor termeni generici izolați. Exemplu de regresie editorială: în cartonul `UNII ELEVI ÎNVAȚĂ ÎN SISTEM DUAL: ȘI LA ȘCOALĂ, ȘI LA MUNCĂ`, `SISTEM DUAL` are prioritate conceptuală față de `ELEVI ÎNVAȚĂ`.
- Folosește exclusiv secvențe **literale**, contigue din DOCX; nicio reformulare, nicio invenție. Subtilitatea semantică este evaluată distinct de succesul tehnic Orange/Bold; preferă puține accente precise.
- Nu sacrifica compactarea în două rânduri doar ca să păstrezi un concept pe un singur rând; fiecare token evidențiat trebuie asociat corect poziției lui MOGRT chiar dacă expresia traversează o delimitare vizuală.
- Următoarele optimizări sunt în stadiu **cerință / candidat**, nu deja instalate în R2.0.4.


## R2.0.7 — regim Strikethrough în subtitrări (cerință aprobată 28.10.2026)
- Modulul **02 Subtitrări** are bifă suplimentară, **implicit DEZACTIVATĂ**: `Omite textul tăiat (Strikethrough) din DOCX`. Activată: în fiecare CUT se ignoră **doar caracterele marcate Word Strikethrough / Double Strikethrough**; textul italic, bold, underline și normal rămâne, în ordine. Nu elimina automat text italic reporter ca și cum ar fi tăiat. DOCX original este read-only.
- Implementarea trebuie să lege textul CUT de caracterele formatate din **paragraful/range-ul exact al sursei DOCX**; dacă textul parserului nu se poate alinia unic la Word, STOP înainte de inserarea pe V3. Nu ghici bazat pe aparență/poziții și nu reformula. Când un CUT este complet tăiat, omite doar acel CUT și raportează `CUT-xx`. Dacă nu mai rămân subtitrări, STOP.
- Politica `INCLUDE_STRUCK` vs `OMIT_STRUCK` face parte din hash/identitatea planului și trebuie verificată între DOCX → generator → CEP → Premiere. Schimbarea bifei în timpul generării/inserării invalidează planul și declanșează oprire/rollback (fără suprascriere). Numără caractere/CUT-uri omise fără a afișa text privat în raport.
- **Ambele moduri** 02 trebuie să respecte opțiunea înainte de Stable. Candidatul R2.0.7 implementează deocamdată numai modul Independent; în Synced checkbox-ul este indisponibil până la integrarea în motorul legacy, pentru a nu crea impresia falsă că funcționează. Nu publica Stable cu bifa falsă în Synced.
- 01 Montaj rămâne speech-first ASR, cu zero fallback brut la TC. **Nu transforma automat textul tăiat din DOCX în sincron de montaj eliminat** fără o politică editorială aprobată separat: opțiunea de aici este cerută explicit pentru Subtitrări 02.


## REGULĂ NOUĂ R2.0.9 — nu confirma Strikethrough 0/0 când bifa este activă (28.10.2026)
- Caz LIVE de regresie: 02 Independent / `Omite textul tăiat` ON, dar status `READBACK PASS: 43 MOGRT pe V3 — SCRIPT_PREVIEW`, urmat de `Omise 0 caractere tăiate în 0 CUT-uri`; Program Monitor încă arăta `Vreau să mă dezvolt în profesia dată.` care este tăiată vizual în DOCX. Aceasta reprezintă **EȘEC**, nu PASS.
- Detectorul trebuie să verifice formatarea Word OOXML: `w:strike` și `w:dstrike`, on/off boolean, direct, character style + `basedOn`, paragraph style + `basedOn`, `w:docDefaults`; text în hyperlinks și `w:del`/`w:delText` din Track Changes. Valoarea FALSE explicită poate suprascrie moștenirea; într-un strat cu `dstrike=true` împreună cu `strike=false`, TRUE câștigă pentru marcajul vizual de dublă tăiere.
- Dacă userul activează `Omite Strikethrough` și rezultatul detectorului are **0 caractere tăiate recunoscute** în sincronurile prelucrate, se produce `STRIKETHROUGH_NOT_DETECTED` și **STOP înainte de importul V3**. Nu se raportează `READBACK PASS`, nu se maschează eșecul, nu se inventează omisiuni. Pentru DOCX fără tăieri, userul poate debifa; nu ghici ce text să elimini.
- Dacă textul parserului nu se aliniază unic cu datele de formatare Word, folosește `STRIKE_FORMAT_AMBIGUOUS` / `STRIKE_FORMAT_UNSUPPORTED` și STOP, nu elimina bazat pe text asemănător. DOCX și proiectele originale rămân nemodificate; V3 deja ocupată NU se șterge/reconstruiește automat.
- Fixul R2.0.9 este numai în modulul Python de citire `tools/r207_docx_strike.py`. 01/03/04/05, MOGRT, montajul și CEP UI NU se rescriu în acest hotfix.


## R2.1.0 — 02 subtitrări, două faze obligatorii înainte de V3 (28 octombrie 2026)
- INCIDENT utilizator: R2.0.7/2.0.9, `Omite textul tăiat` activată, dar a rămas subtitrarea cu propoziția tăiată; niciun `READBACK PASS` pentru numărul de grafici nu înseamnă certificarea filtrării DOCX.
- **REGULĂ UX P0:** modulul 02 Independent funcționează în 2 etape explicite: (1) **`Analizează DOCX`**, citește fișierul din modulul 00, bifa ON/OFF, formatările Word și construiește numai planul local; afișează numărul de cues, CUT-urile schimbate, numărul de caractere omise și, pentru fiecare CUT schimbat, textul **`ÎNAINTE`** / **`DUPĂ`**; nu trimite comenzi Premiere în faza 1; (2) **`Inserează subtitrările verificate pe V3`**, inițial DEZACTIVAT, se activează numai după analiza locală complet validată și verificabilă.
- **Bifa**: OFF implicit include tot textul. ON păstrează italic și orice text netăiat; dacă motorul detectează **0 omisiuni**, `STRIKETHROUGH_NOT_DETECTED` și STOP înainte de V3. Nu insera 43 de MOGRT cu `Omise 0` și succes fals. Dacă nu se pot potrivi unic fragmentele Word, `STRIKE_FORMAT_AMBIGUOUS/UNSUPPORTED` + STOP.
- **Integritate**: DOCX SHA-256, hash plan JSON, opțiunea bifei și `generatorVersion` trebuie verificate din nou imediat înainte de Premiere și la fiecare MOGRT. Dacă DOCX, bifa, planul sau motorul Python se schimbă după analiză, invalidează previzualizarea și cere reanalizare. Un motor vechi va fi refuzat cu `ENGINE_VERSION_MISMATCH`.
- Modurile 01/03/04/05, executorul Premiere, track guards și V5 ocupată NU se schimbă. În 02 Synced, bifa rămâne dezactivată până la integrare exactă în motorul sincronizat. Nu șterge V3 existentă automat.
- Textul DOCX PRIVAT se afișează numai local în panou și se salvează numai în Temp sub hash DOCX, niciodată în repo GitHub, notificări sau loguri externe.


## R2.1.1 — Modul 02: un click, analiza internă și subtitrări lizibile (28.10.2026)
- Utilizatorul a CONFIRMAT că filtrarea Strikethrough funcționează la R2.1.0. Noul UX aprobat elimină butonul suplimentar `Analizează DOCX` și previzualizarea „ÎNAINTE/DUPĂ” din interfață. În 02 Independent rămân numai controalele necesare: selectorii de mod/poziție, bifa `Omite textul tăiat (Strikethrough) din DOCX` (OFF implicit) și **UN SINGUR** buton `Inserează subtitrările`.
- La apăsarea unicului buton, motorul efectuează OBLIGATORIU două faze INTERNE, serializate: (1) parsează DOCX, aplică politica Strikethrough, verifică formatările, hash-ul DOCX, versiunea motorului, auditul de omisiuni și hash-ul planului local; (2) numai la PASS execută preflight V3 și inserează sub controlul preflight/rollback existent. Etapa (1) nu trebuie să facă niciun apel Premiere. Nu afișa butoane adiționale sau dialoguri de confirmare pentru textul eliminat; statusul/progresul rămân vizibile.
- Dacă bifa e ON dar numărul de caractere tăiate identificate este zero, STOP `STRIKETHROUGH_NOT_DETECTED` înainte de orice inserare. Dacă Word/plan/checkbox/mod/poziție se schimbă în timpul analizei sau inserării, STOP + rollback conform numărului deja inserat. Nu modifica V3 ocupată automat.
- **Subtitrări lizibile 02:** toate textele în română trebuie împărțite în MAX 74 caractere per MOGRT, fără despărțirea cuvintelor, fără pierderea, adăugarea sau parafrazarea textului DOCX. Preferă ruptura la semn de sfârșit de propoziție (`.`, `!`, `?`, `…`) când este posibil; începutul unei propoziții noi **nu rămâne cu 1–2 cuvinte la finalul subtitrării anterioare**. Exemplu real de regresie: `... Și astfel noi reușim să suplinim planul de admitere. Să` este invalid; `Să informăm tinerii...` începe următorul MOGRT. Evită și cuvintele de legătură lăsate singure la final (`să`, `și`, `dar`, `de`, `că` etc.).
- În 02 Synced, logica stabilă rămâne neatinsă și bifa Strikethrough dezactivată până la suport în motorul sincronizat. 01 Montaj, 03 NameTag, 04 Cartoane, 05 VO HOLD și executorul MOGRT NU sunt modificate de R2.1.1. Nu promova la Stable fără test Premiere LIVE.


## REGULĂ R2.1.2 — subtitrări echilibrate fără resturi (28 octombrie 2026)
- Feedback LIVE utilizator: R2.1.1 a mutat corect `Să informăm...` pe subtitrarea următoare, dar a rămas cazul `Să informăm tinerii că ei pot să studieze mai departe, dar să` / `nu stea acasă.`: primul cue prea plin, al doilea 15 caractere. Se impune o segmentare editorială nouă, folosind sens, lungime, punctuație și echilibru.
- **Obiectiv**: la împărțirea unui CUT în 2+ subtitrări, căutăm fragmente cu lungimi apropiate, fără cozi de 1–3 cuvinte, dar păstrăm sintagma naturală și regula propoziției noi. Exemplu testat: `Să informăm tinerii că ei pot să studieze` (41 caractere), apoi `mai departe, dar să nu stea acasă.` (34 caractere). Propozițiile scurte complete, de sine stătătoare, NU se fragmentează.
- **Algoritm**: segmentare prin cuvinte întregi (max 74 caractere, fără text schimbat), căutare de minime globale între limitele CUT-ului, cu penalizări pentru dezechilibru, cozi foarte scurte și amestecarea unor propoziții semnificative; priorități pentru `.`, `?`, `!`, `…`, `,`, `;`, `:` și introduceri de clauze. Evită a lăsa la final `să`, `și`, `dar`, `de`, `că`, `nu`, `pot`, `mai` etc. Poate adăuga **cel mult un** cue față de minimul necesar, doar dacă altfel s-ar forma resturi nefirești.
- **Invariante**: `clean(' '.join(chunks)) == textul aprobat din DOCX după filtrarea Strikethrough`, 1–74 caractere/cue, nu tăia cuvinte, nici parafrază/invenție/omisiune. Respectă Italic reporter / Regular intervievat, independența 02 vs 01, `SCRIPT_PREVIEW`, timpii/editorial safe V3. Un singur buton `Inserează subtitrările` + bifa, analiza DOCX obligatorie intern.
- Nu aplica algoritmul de titrare V3 la NameTag V4 sau Cartoane V5; nu afecta 01 Montage, 05 VO HOLD ori executorul MOGRT.
- Funcția viitoare **„Învață din corecturile mele”** este rezervată ca modul separat, **NU inclusă în R2.1.2**. Cerința completă și gate-ul de aprobare umană sunt în `docs/EDITOR_FEEDBACK_LEARNING_SPEC_RO.md`. Citirea timeline-ului trebuie să fie READ-ONLY, diferențele să fie aprobate explicit de editor înainte de învățare/test/release.


## R2.1.3 — Montaj 01: recuperare strictă pe transcript audio existent (28 octombrie 2026)
- Incident real: în Bubuieci, Montaj 01 a oprit `8/17` sincronuri fără potrivire sigură (CUT-uri 9931/9980/9930/9937/9974). Acest STOP nu este defectul de siguranță; problema este recuperarea insuficientă a ASR.
- Modulul nou `tools/r213_second_pass.py`, invocat din `tools/r193_pipeline.py` numai pentru sincronuri cu potrivire slăbită, caută a doua oară în **cuvintele transcrise din audio real**, fără a schimba DOCX/clipurile sau a transcrie inventat. Cere text aproape integral (similaritate de cel puțin 0.88), primele și ultimele două cuvinte ca ancore, rezultat unic în sursă și drift la max 75 s. Reporter TC e NUMAI reper de căutare ±90 s. Potrivirile repetate/fragmentare scurte/audio absent intră în REVIEW.
- Nu se relaxează pragurile originale R1.9.13 (`MIN_BOUNDARY_SCORE=.67`, `MIN_FULL_TEXT_SCORE=.67`) și nu se eludează `r143_build.is_safe`, `validate_speech_only` ori `old_write` fail-closed. R2.1.3 poate propune `REVIEW_SUGGESTED`, nu se poate declara singur `AI_MATCHED`.
- Pentru CUT-uri rămase nesigure după R2.1.3, următoarea etapă este retranscrierea selectivă cu FFmpeg/Whisper pe ferestre sursă și comparație ASR independentă, folosind laboratoarele R2.0.6, **nu fallback reporter TC**; toate trebuie testate local în Premiere pe o COPIE înainte de Stable.
- Păstrează un singur buton `Montează după scenariu` și status clar. Dacă nu toate CUT-urile sunt valide, NU modifica timeline V1/A1. Modulele 02/03/04/05 rămân nemodificate.


## UPDATER Beta — reguli Windows cp1252 pentru metadata GitHub (28.10.2026)
- Incident Premiere UI: apăsarea `Verifică actualizări Beta` a afișat `Răspuns Beta invalid` cu `UnicodeEncodeError: 'charmap' codec can't encode character '\\u0103'`. Asta este eroare de codare a ieșirii consolei Python din updaterul Windows, nu eroare în planificatorul Montaj 01 sau în arhiva R2.2.0.
- Diagnostic GitHub CI `40733313033` a confirmat că metadatele mai multor prerelease-uri (inclusiv v2.1.2 / v2.1.1) includeau `ă` U+0103 și v2.2.0 includea `ț` U+021B, neencodabile în cp1252.
- Remediu server-side CI `40733478710` SUCCESS: normalizare titluri și note ale prerelease-urilor GitHub la ASCII, fără a schimba ZIP-urile sau tag-urile, ZIP v2.2.0 SHA256 `2dec078fa67cd75de67a24090d20258720cd8b88a48672d4eebbfae64002b00c` **identic**; Stable R1.9.13 rămâne neatins. API releases încă ordonează v2.2.0 primul.
- Remediu structural obligatoriu pentru următoarea versiune: process spawn Python din CEP Beta updater trebuie să seteze `PYTHONUTF8=1` și `PYTHONIOENCODING=utf-8`, iar Python trebuie să folosească `sys.stdout.reconfigure(encoding='utf-8',errors='backslashreplace')` sau `json.dumps(...,ensure_ascii=True)`. Metadatele trebuie să fie independente de codepage. Nu există încă LIVE confirmation că retry-ul instalării reușește; nu pretinde asta până la captura din Premiere.


## REGULĂ UPDATER R2.2.1 — ieșire ASCII-safe / UTF-8 Windows (28.10.2026)
- Cod Python care scrie JSON pe stdout pentru CEP trebuie să folosească `json.dumps(...,ensure_ascii=True)` pentru rezultate ȘI erori, indiferent de locale; altfel `UnicodeEncodeError` ascunde eroarea reală și cade `Răspuns Beta invalid`.
- Toate subprocess-urile Python pornite din CEP trebuie să seteze **explicit** `env:Object.assign({},process.env,{PYTHONIOENCODING:'utf-8',PYTHONUTF8:'1'})` sau echivalent verificat, fără să schimbe sistemul în întregime. Erorile locale trebuie raportate prin JSON parsabil, nu prin traceback stderr incomplet.
- Remediul permanent a fost publicat ca v2.2.1 Beta https://github.com/Sankio9/ai-video-editor-updates/releases/tag/v2.2.1 (doar două fișiere, SHA exact, rollback), după test CI `40734874138`. Următorul release rămâne Beta până la confirmarea LIVE în Premiere.

## R2.3.0 — 02/03/04 Independent din scenariu (2026-10-30)
- DOCX heterogene: SINCRON/VOX/SOT, cod 4 cifre, timecode punct/două puncte sau lipsă, cartoane uppercase și explicite, GEO/ambianță, document Word cu tabele.
- Fiecare modul trebuie să ruleze fără Montaj 01, fără media în Project Panel, fără raport R143/R220, fără ASR. 02=SCRIPT_PREVIEW, 03/04=EDITORIAL_PREVIEW; nu eticheta ca audio-sincronizat.
- Parserul nou R230 e fallback strict numai la neidentificarea declarațiilor/cartoanelor; parserul aprobat rămâne prioritar. 74 char 02; doar nume+funcție pentru 03; 33 char/linie 04. Nu inventa identități ori cartoane absente.
- MOGRT 02 V3, 03 V4, 04 V5; fără QE; preflight, readback, rollback, acceptare explicită, protecția V5 și Stable R1.9.13 sunt neschimbate.
- Corpusul utilizatorului: nouă DOCX analizate local, inclusiv celule de tabel și Strikethrough. Nu pune surse private în GitHub. Document complet: `docs/R230_DOCX_FORMATS_INDEPENDENT_RO.md`. Release Beta `v2.3.0`, LIVE Premiere neconfirmat.

## R2.3.1 — contract permanent CEP/Python pentru module independente (2026-10-30)
- Bug LIVE: `ENGINE_VERSION_MISMATCH` în 02/03 după R2.3.0 pentru DOCX 29.10 vox. Cauza **confirmată din codul release-ului real**: `cep/r20_panel.js` permitea doar generator `R2.1.1-auto-preflight-readable`; noul `r230_universal.py` întorcea `R2.3-UNIVERSAL-DOCX-9-FORMATS`. În plus, noul parser folosea `KEEP_ALL` în loc de `INCLUDE_STRUCK` și nu întorcea `NOT_APPLICABLE` pentru 03/04.
- Remediere v2.3.1: update **atomic pentru două fișiere SHA-pinned** `cep/r20_panel.js` + `tools/r230_universal.py`. Panoul acceptă strict R2.1.1 legacy sau R2.3 numai dacă SHA scriptului R230 corespunde cu cel aprobat și raportul Python/planului are aceeași versiune. Politicile `INCLUDE_STRUCK`, `OMIT_STRUCK`, `NOT_APPLICABLE` coincid acum cu contractul deja verificat. Nu se dezactivează condițiile de securitate.
- Pentru ORICE release viitor care schimbă generatorVersion / politici / schema JSON, publisherul TREBUIE să includă simultan compatibilizarea panoului și un test real `DOCX → Python main stdout + JSON → CEP contract` pentru toate 02/03/04. Release-ul cu parser nou și panou incompatibil este **interzis**.
- R2.3.1 nu modifică executor MOGRT JSX, timeline, Montage 01, 05, Stable R1.9.13; LIVE Premiere V3/V4/V5 încă necesită readback ca să fie acceptat.

## R2.3.2 — Reguli editoriale obligatorii 02/03 pentru Word DOCX (30 octombrie 2026)
- **Speaker turn**: niciodată text Regular (intervievat) și Italic (reporter/narator) în același MOGRT. Word runs se grupează doar dacă au același stil. Fragmentul italic \`Da.\` devine un CUT de subtitrare individual între textul Regular al intervievatului; nu se atribuie identitatea ultimului intervievat unei replici Italic.
- **CN (comentariul naratorului)**: dacă textul obișnuit nu este \`CARTON\`, nu este SOT/VOX/SINCRON, nu are o sursă/un vorbitor confirmat, este subtitrare **Italic**, fără NameTag, inclusiv într-un paragraf normal după \`PKG\` sau în coloana dreaptă a unui tabel Word cu GEO/metadata în stânga. Conținutul din celula DREAPTA continuă și când celula STÂNGA a rândului este goală. Codurile sursei, datele GEO, creditul Facebook/X și descrierile de imagine nu se subtitrează ca replici.
- **SOT/VOX/SINCRON**: text Regular, cu NameTag numai când există o pereche explicită **nume + funcție**. Textul de sincron în Bold dintr-un tabel Word rămâne Regular; persoana Gulmira Aslanova / mamă primește NameTag, în timp ce CN \`Fetița din imagine...\` este Italic și nu primește NameTag. Un vorbitor fără identificare verificată poate primi subtitrare Regular, dar nu burtieră inventată.
- **Notificare NameTag**: nu mai folosi \`window.confirm\` cu mesaj trunchiat. O singură fereastră modală conține lista integrală CUT-ID, sursă, paragraf, motiv (scroll dacă sunt multe), numărul de NameTag confirmate și exact opțiunile **Continuă — omite N** / **Oprește**; Escape înseamnă Oprește. Nicio inserare V4 înainte de confirmarea explicită. Siguranța V4 și rollback rămân.
- 02 și 03 continuă independent de Montaj 01, \`SCRIPT_PREVIEW\` în absența ASR. Nu interpreta aceste subtitrări ca sincronizare audio verificată.
- Release Beta \`v2.3.2\`, două fișiere SHA-guarded: \`tools/r230_universal.py\`, \`cep/r20_panel.js\`. MOGRT JSX, V3/V4/V5 protections, 01, 05, updater, Stable R1.9.13 nemodificate. Testele automate trecute; LIVE Premiere încă de verificat.

## R2.3.3 BETA — safe empty-independent DOCX and editorial content diagnostics (2026-10-30)
- Screenshot LIVE on installed R2.3.2: all 02/03/04 yielded unhandled `ValueError` from `tools/r230_universal.py` with phrases `Nu sunt declarații pentru subtitrări`, `Nicio burtieră validă` and `Nu există cartoane`. This happened **before** any Premiere JSX; V3/V4/V5 remain untouched. Screenshot does NOT show which DOCX was selected in section 00, so exact failed DOCX identity is unconfirmed.
- R2.3.3 published <https://github.com/Sankio9/ai-video-editor-updates/releases/tag/v2.3.3> (BETA prerelease) from successful CI release run `41030862629`. ZIP SHA-256 `49f7b50a6ec145e681d0ded7a5aa5d3f9133e827a93db78cec0a2447ae2ddcd3`, 21401 bytes. Strict before SHA from v2.3.2 for **only** `cep/r20_panel.js` and `tools/r230_universal.py`; current Python source SHA re-pinned by CEP handshake, no global SHA checks disabled. JSX/MOGRT, 01, 05, updater, Stable v1.9.13 unchanged.
- Fallback parser returns schema-correct 0-item plan and `contentSummary` (DOCX basename, paragraphs, table rows, declarations, explicit name+role and cartons) instead of throwing when nothing relevant is detected. CEP status `NIMIC DE INSERAT` for corresponding module; immediately stops prior to preflight/insert/rollback. The lack of a NameTag/carton isn't automatically a failure; never fabricate.
- Conservative plain-CN 02: when an explicit `SCENARIU`/related heading exists OR 3 substantive plain narrative paragraphs are present, offer Italic CN editorial previews; prompt approval prior to insert V3. Unmarked text is NOT treated as verified audio sync. 03/04 never infer identity or carton solely from narrative prose.
- Regression run `41030621990` and release run `41030862629` SUCCESS: module 02/03/04 no-applicable output; marked CN with manual approval gate, article teaser no implied clips, original explicit speaker/CARTON content, 26-CUT scrollable NameTag modal, exact asset SHA, no JSX changes. **No Adobe Premiere LIVE after 2.3.3 observed.**
- Next step is concise LIVE test using DOCX currently selected in 00 and 02/03/04; avoid unnecessary re-upload or repeated montage tests. If zero material is reported for a document known to have eligible speech, read `contentSummary` and inspect relevant DOCX markers/table columns; implement source-specific detection, NOT just suppress error. A safe zero item result does not satisfy a request to produce required captions.

## R2.3.4 — verificare pe DOCX real cu 6 coloane Word (2026-10-30)
- User LIVE screenshot R2.3.3: DOCX `2026.10.15 video scoli azere.docx` a fost diagnosticat `paragrafe: 1; rânduri tabel: 0; declarații: 0; identități: 0; cartoane: 0`. User a atașat `2026.10.15 video scoli azere(1).docx`. **Cauza reală identificată local în fișierul anexat**: documentul conține 5 paragrafe de body și **un tabel Word cu 21 de rânduri și 6 coloane fizice**; sursele/GEO sunt în celule unite 0–1, narațiune/CN și SOT în celule unite 2–3, ultimele 4–5 sunt goale. R233 folosea `row.cells[-1]`, deci elimina 100% din conținut și raporta fals zero.
- Inspecția DIRECTĂ a documentului privat cu python-docx (fără upload pe GitHub) a verificat **14 rânduri editoriale după PKG** și **17 paragrafe de narațiune/sincron** din celulele 2–3, inclusiv un rând numai cu conținut în dreapta, și **trei perechi de NameTag explicite**: Gulmira Aslanova/mamă, Elnara Akimova/Deputată, Sanubar Heidarova/Sociolog. INTRO, GEO, Facebook/X, Reuters/B-roll sunt metadate sursă; CN trebuie să fie Italic fără NameTag, SOT cu nume+funcție Regular cu NameTag. Nu există cartoane editoriale explicit marcate, deci zero V5 este editorial corect.
- R2.3.4 actualizează `paragraphs()` în `tools/r230_universal.py`: dedup celulele unite după același element XML, intră în conținut după rândul PKG (exclude INTRO), folosește indexul fizic al primei celule populată din jumătatea editorială a tabelului, nu ultima celulă goală; păstrează rândurile cu stânga goală, formatarea Word Bold/Italic și cele două coloane clasice.
- Release BETA v2.3.4: https://github.com/Sankio9/ai-video-editor-updates/releases/tag/v2.3.4 ; release CI `41033553885` PASS, regression CI `41033317158` PASS; SHA256 ZIP `d631e5f7af8a9246b8f04c1f28e57c0f620bd83f7f4616b46a9215eb51a554bf`, 21696 bytes, strict before/after SHA din v2.3.3; DOAR `cep/r20_panel.js` (version + SHA handshake), `tools/r230_universal.py`. Stable v1.9.13, MOGRT JSX, 01, 05, updater, safety preflight/rollback neschimbate.
- CI sintetic cu structura tehnică a documentului real: tabel 6 coloane, merged 0–1 și 2–3, empty 4–5, INTRO/PKG, text CN pe rând cu stânga goală, 3 SOT cu nume+rol: 02 = 9 elemente, 03 = 3, 04 = 0 fără inventat. Regression pe tabele clasice 2 coloane și modal NameTag scroll 26 CUT-uri. CI NU reprezintă test LIVE Premiere. User nu trebuie să reîncarce DOCX și nu trebuie să refacă Montage 01. În Premiere după instalarea R234 verificați în 02/03 pe o secvență de test; V3/V4 readback și timing editorial încă necesită validare LIVE.
