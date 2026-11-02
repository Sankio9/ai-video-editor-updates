# AI Video Editor — STABLE AUTONOM, specificație tehnică (RO)

**Versiune document:** 0.1 · **Data:** 2026-11-02 · **Statut:** SPEC APROBATĂ CA DIRECȚIE, NU SOFTWARE IMPLEMENTAT
**Decizii explicite utilizator:** procesare 100% locală/offline, internet exclusiv la actualizări solicitate; distribuție privată pentru echipă; Windows și macOS; Premiere Pro 2025+; Beta nu se modifică.
**Sursă editorială:** `docs/AI_VIDEO_EDITOR_MASTER_SPEC_RO.md`, `docs/ACCEPTANCE_TESTS_RO.md`, `docs/R230_DOCX_FORMATS_INDEPENDENT_RO.md`. Acest document este o **specificație separată** pentru noua ediție fără Montaj 01/VO 05, NU o înlocuire a contractelor Beta sau o promovare a R1.9.13.

## 1. Produsul livrat

**AI Video Editor — Stable Autonomous / Private Team Edition**

Panoul conține EXACT cinci secțiuni vizibile:
1. **Actualizări** — versiunea instalată, „Verifică actualizările”, note, descarcă și instalează prin mecanismul Adobe, rollback ghidat.
2. **Scenariu** — un singur DOCX selectat o dată, stare analiză, format, diagnostic editorial cu acoperire și erori clare.
3. **Subtitrări (V3)** — un buton de inserare; opțiune „Omite textul tăiat (Strikethrough)”, mod preview independent; sincronizat numai cu ancore de timeline confirmate.
4. **NameTag / Burtieră (V4)** — nume + funcție verificabile, o inserare per bloc/reintroducere editorială.
5. **Cartoane VO (V5)** — exclusiv textul editorial al cartoanelor din Word, layout compact și accente aprobate.

**Exclus definitiv din această ediție:** Montaj 01, analiza/ASR audio, Whisper, FFmpeg, Python, subprocess, matching audio, VO 05, agenți AI/cloud, login pentru utilizarea de zi cu zi, telemetrie. Acestea pot continua numai în Beta și NU sunt dependențe ascunse ale Stable. „Sincronizat” este disponibil doar când există ancore validate în secvență; altfel este afișat **SCRIPT_PREVIEW / nesincronizat**, fără a pretinde potrivire audio.

## 2. Contract offline / portabilitate

- Precondiții acceptate: Adobe Premiere licențiat și componentele lui standard (inclusiv Creative Cloud necesar instalării/activării). **Fără runtime separat** pe PC/Mac: nu cere Python/Node/Whisper/Terminal/PowerShell/CLI, serviciu localhost, server, cloud, proces agent, configurare manuală a variabilelor de mediu.
- Panoul, motorul DOCX, regulile editoriale, librăriile JS permisive (cu licențele lor), șabloanele MOGRT și verificatorul actualizărilor se livrează în pachet. Un singur artefact distribuit per platformă/tehnologie (nu „instalează dependent X”).
- Toată analiza DOCX și generarea planului rulează **fără internet**; aplicația NU accesează URL-uri, nu trimite documente, metadate media ori conținut la serviciu extern. În lipsa conexiunii, toate modulele 00/02/03/04 funcționează; Actualizări afișează starea fără a bloca munca.
- DOCX-uri de lucru și loguri rămân pe dispozitiv. Nu publicăm documente, audio, transcrieri, nume sau căi private în GitHub. Pentru support exportăm doar diagnostic redactat/anonimizat după acceptul utilizatorului.
- Căile fișierelor se tratează nativ pe Windows/macOS; inclusiv diacritice, Unicode NFC, spații, foldere cu nume lungi și directoare de rețea accesibile. Starea este izolată per proiect/DOCX SHA, fără referințe `D:\AI-Video-Editor` sau slash-uri hardcodate.
- MOGRT-urile trebuie auditate pentru dependențe efective: After Effects, fonturi, pluginuri terțe și Creative Cloud Fonts. **Nu declarăm „Premiere-only” înainte de un test real pe un sistem curat cu numai Premiere/Creative Cloud.** Dacă un MOGRT necesită ceva extern, se rezolvă prin șablon portabil compatibil vizual sau se raportează BLOCKED. Nu împachetăm fonturi fără drepturi de redistribuire.

## 3. Arhitectură

```
DOCX ales de utilizator
  ↓
CORE editorial pur JavaScript/TypeScript (fără OS APIs)
  ├─ OOXML/ZIP local: paragrafe, tabele, celule unite, run-uri, TC, italic, strike
  ├─ clasificare: metadate vs AMB/SOT vs narator CN vs V5 VO
  ├─ verificare acoperire editorială și excepții explicite
  ├─ layout: V3 74 caractere, V4 bloc identificare, V5 28–29 / max. 4 rânduri
  └─ PLAN JSON imutabil + DOCX SHA + checksum conținut + semantica PREVIEW/SYNCED
  ↓
ADAPTER Premiere {capabilities, preflight, insert, readback, rollback}
  ├─ CEP + ExtendScript (compatibilitate imediată)
  └─ UXP (migrare viitoare; gate separat pentru text MOGRT)
  ↓
V3 · V4 · V5 (fără V1/A1 și fără QE)
```

**CORE JS obligatoriu:** parser OOXML portat din motorul R2.3.x în cod pur JS testabil cu Node doar în CI/build, **nu Node instalat de utilizator**. Bibliotecile ZIP/XML se includ integral în pachet, cu pinned versions, audit de licență și limite anti zip-bomb. Se citesc `word/document.xml`, `w:p`, `w:tbl`, `w:tr`, `w:tc`, `w:r`, `w:br`, `w:tab`, `w:i`, `w:strike`, merged cells, fără network fetch la `external relationships`. Cazurile OOXML complexe/Track Changes ambigue se raportează REVIEW; nu se deduc automat.

**Parserul produce manifest de acoperire:** nr. paragrafe eligibile, cod sursă, ordinal, replici, CN, identități cu rol, cartoane, fragmente eliminate prin Strike, fragmente ambigue, input SHA. **Niciun pasaj eligibil omis în tăcere.** Un plan parțial trebuie să raporteze lista exactă și să ceară aprobare editorială înainte de orice inserare; nu numește `SUCCESS` un plan incomplet.

**CEP adapter:** păstrează executorul MOGRT aprobat și verifică semnăturile/parametrii reali din Premiere. **UXP adapter:** nu migra automat după sintaxă; implementare numai după probe concrete de import, acces parametri text, stiluri, readback și rollback pentru toate cele trei MOGRT. Core și adaptoarele au contract de date identic; testele editoriale pot fi comune.

## 4. Compatibilitate și calendar tehnologic Adobe

- **Premiere 2025:** în familia 25.x există ediții anterior lui 25.6; UXP pentru Premiere devine disponibil de la **25.6**. Pentru 25.0–25.5 folosim CEP dacă API și manifest/testele reale îl permit.
- **Premiere 25.6+ / 2026+**: CEP este o punte temporară; UXP trebuie urmărit ca tehnologie de lungă durată. Adobe a anunțat CEP dezactivat implicit în Premiere începând din decembrie 2028 și eliminat din versiunile Creative Cloud lansate după noiembrie 2029. Așadar NU promitem că pachetul CEP va continua să funcționeze după acest prag.
- **MOGRT/UXP:** accesul complet la text/parametri MOGRT avea limitări confirmate de Adobe la 25 august 2026. Gate obligatoriu de compatibilitate API real înaintea lansării unui adapter UXP; dacă lipsește, rămânem pe CEP pentru versiunile care îl suportă sau dezvoltăm alternativă proprie vizual echivalentă, după aprobare.
- Matrice suportată **numai după LIVE PASS**: Windows 10/11 x64 (conform cerințelor versiunii Premiere), macOS Intel și Apple Silicon numai pe versiunile Adobe/OS realmente suportate; Premiere 25.0–25.5, 25.6, ultima versiune curentă. Un test pe Windows nu validează macOS. Pe macOS trebuie probate explicit permisiunile filesystem, extensia semnată, Apple Silicon, sursele/diacriticele și renderul MOGRT.

Referințe Adobe (verificate 2026-11-02):
- https://developer.adobe.com/premiere-pro/uxp/introduction/
- https://helpx.adobe.com/creative-cloud/apps/integration-with-other-apps/manage-plugins/cep-uxp-plugin-transition.html
- https://blog.developer.adobe.com/en/publish/2026/09/investing-in-the-future-of-creative-cloud-extensibility-uxp-comes-to-our-flagship-applications
- https://community.adobe.com/questions-729/uxp-source-text-param-on-ae-adbe-text-returns-no-value-other-21-params-on-the-same-component-work-1638103

## 5. Reguli editoriale comune V3/V4/V5

**00 Scenariu:** un DOCX la un moment dat; orice modificare de conținut invalidează planuri vechi. Parser fără întrebări repetate; afișează analiza (ex: 8 SOT, 5 blocuri VO, 6 NameTags) și REVIEW explicit.

**02 V3:** text editorial **exact**; max 74 caractere/cue; persoană Regular, întrebarea reporterului și narator CN Italic și cue separat; ambianță fără NameTag; identități, roluri, coduri, GEO, URL, timpi și title nu se afișează ca subtitrări; Strikethrough ON elimină doar părțile tăiate. În independent durata este estimată de lectură, cu indicație persistentă **SCRIPT_PREVIEW**. **Sincronizarea audio nu este produsă de această ediție**.

**03 V4:** nume+rol explicit, un MOGRT per bloc, inclusiv reintroducere după cod sursă nou; roluri precum `beneficiar`, `medic de familie`, `muncitor în construcții`, nume unice acceptate dacă rolul e în DOCX. Numai AMB fără identitate: SKIP. Ambiguitatea identificării: REVIEW, fără inventare.

**04 V5:** numai blocuri declarate/capitals; text integral, max. 28 preferat, hard-max. 29 caractere vizibile/rând, până la 4 rânduri/MOGRT, pagination dacă nu încape, Orange/Bold în stilul aprobat; probe **16:9 și 9:16** pentru safe-area efectivă. Nu genera cartoane dintr-un sincron cu majuscule; nu transforma rolul în VO.

**Timpi/pozitie:** independent oferă „De la începutul pistei” și „După ultimul element” (fără să rescrie alte materiale). Pe montaj existent, sincronizarea este activată NUMAI dacă există markere/ancore real validate compatibile cu DOCX. Fără ele, explică indisponibilitatea și nu pretinde sync.

**Protecția Premiere:** piste existente V3/V4/V5; preflight inventar complet tip/nume/interval, lock și coliziuni; confirmare înainte de modificări, readback pe fiecare inserare, rollback verificabil sau STOP fără mutație. V5 ocupată: două opțiuni inteligibile; dacă nu există cale dovedită de suprascriere sigură pe copie cu rollback, butonul destructiv rămâne dezactivat și explicat. Fără QE, fără creare de piste și fără modificări V1/A1.

## 6. Împachetare și distribuție privată

- **CEP:** extensie semnată **ZXP**, identificator diferit de Beta pentru testele de dezvoltare, instalare gestionată de instrumentele Adobe/Creative Cloud în profil per utilizator, fără modificarea directă a directorului versiunii Beta. Pentru Stable final: migrare controlată de la Stable R1.9.13 numai cu backup și rollback.
- **UXP:** pachet **CCX** pentru Premiere 25.6+ când va fi funcțional. CCX poate fi instalat prin Creative Cloud Desktop; separat de ZXP. Pentru distribuția echipei nu este necesară listare în Marketplace. Nu livra pachete dezvoltator nesemnate în exploatare.
- Pachetele conțin inclusiv MOGRT-urile aprobate, licențe și checksum-uri. Fără căi absolute. Orice dependență externă identificată (font/plugin) este blocant de lansare până la eliminare/testare.
- **Distribuția privată:** recomandat repository/release **privat** separat de Beta și acces de citire doar pentru membrii echipei. Nu stoca token PAT personal în extensie. Fluxul de autentificare pentru consultarea release-urilor private trebuie proiectat și validat, sau se folosește un URL intern de distribuție autorizat. Fără autentificare obligatoare pentru rularea modulelor offline.

## 7. Updater Stable, separat de Beta

- Stable consultă numai canalul/tagurile **Stable Autonomous**, niciodată Beta/prerelease. Verificarea la apăsarea utilizatorului; conexiunea nu este folosită la deschiderea panoului.
- Release: manifest semnat **Ed25519** cu cheie publică pinned în plugin + SHA-256 pentru fiecare pachet/fișier, număr monoton de release, compatibilitate host/OS, minimum version, listă explicită. Semnarea are loc în CI; cheile private NU intră în repo/artefact sau în runtime.
- Proces: `check → display changelog → download to sandbox → verify signature, SHA, version/OS → Adobe installer → reopen Premiere → health/readback → success`. Fără executare din ZIP sau patch la întâmplare. O extensie ZXP semnată NU trebuie auto-modificată în directorul instalat (ar invalida semnătura); instalarea se face prin mecanismul Adobe.
- Backup și restaurare: păstrează pachetul anterior valid și configurările per proiect. Dacă instalarea/health-check eșuează, oferă restaurare din pachetul anterior prin installer. **Nu promite actualizare silențioasă „one click” pe ambele OS înainte de a testa restricțiile Adobe/macOS.**
- Nicio reinstalare Beta, nicio copiere între canale, nicio mutare automată a proiectelor utilizatorului. Semnale de eroare clare pentru offline, canal privat fără acces, hash nepotrivit, plugin/host incompatibil.

## 8. Performanță, acceptare și limite

- Un DOCX de format real se analizează în plugin fără procese externe; ținta inițială propusă: **sub 5 secunde pentru scenarii uzuale** (nu criteriu demonstrat încă). UI nu blochează Premiere inutil; progres pentru fișiere lungi.
- Corpus de regresie: șase reportaje structurale deja documentate (Angelus, Muncitori străini, Satul Nou, Cernobîl, Veterinar, Balatina) plus Bubuieci/tabel Word/VOX. Testele conțin fixture-uri sintetice; fișierele reale rămân private.
- Gata de Stable **numai** după matrice `Windows × macOS × Premiere 25.0–25.5 / 25.6 / versiune curentă suportată` și test Premiere real: instalare, funcționare offline, 00, 02 V3, 03 V4, 04 V5, MOGRT text/Orange, preview, safe-area 9:16, collision, rollback, upgrade/rollback și coexistență fără atingerea Beta.
- Registru pentru fiecare test: `LOCAL PASS`, `PREMIERE LIVE PASS`, `FAIL`, `NOT TESTED`, număr versiune/OS/host și hash artefact. CI PASS singur nu înseamnă Stable.
- Cost operațional țintit: **$0/lună infrastructură suplimentară** pentru echipă mică, dacă distribuția internă GitHub/CI rămâne în planul și cotele disponibile; licențele Adobe/Premiere, eventuala semnare comercială sau dependențele MOGRT nu sunt incluse în această estimare.

## 9. Interdicții / limite de mandat

**În această etapă sunt autorizate DOAR documentația și planificarea într-un branch separat.** NU modifica, publica, reinstala sau redistribui Beta, Stable R1.9.13, updaterul curent, branchul `feature/r20-independent-graphics-gate`, fișierele instalate pe PC ori proiectele Premiere. Orice build sau promovare Stable va cere testele și aprobarea editorială corespunzătoare.
