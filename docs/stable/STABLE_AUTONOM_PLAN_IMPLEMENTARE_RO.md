# AI Video Editor — STABLE AUTONOM: plan de implementare și acceptare (RO)

**Data:** 2026-11-02 · **Tip:** plan executabil, fără modificări de cod acum · **Document de bază:** [STABLE_AUTONOM_SPEC_TEHNICA_RO.md](./STABLE_AUTONOM_SPEC_TEHNICA_RO.md)

## Reguli de proiect

- **Stable Autonomous = produs distinct de Beta.** Stable R1.9.13 și Beta R2.3.x sunt **READ-ONLY** până la finalizarea testelor și aprobarea promovării. Dezvoltarea pornește dintr-un branch exclusiv `feature/stable-autonomous-*` sau un repository separat, nu din `feature/r20-independent-graphics-gate`.
- UI fixă: **Actualizări / Scenariu / Subtitrări / NameTag / Cartoane**. Nu adăuga butoane pentru Montaj, ASR, VO sau „Agent AI”.
- **Offline exclusiv:** niciun apel HTTP în fluxurile 00/02/03/04; acces online doar la „Verifică actualizările” sau „Descarcă actualizarea”. Fără Python/node/npm/runtime instalat la utilizator. NPM poate fi folosit numai în dezvoltare/CI.
- **Fiecare fază are criteriu de trecere.** Un build „CI PASS” nu se confundă cu „PREMIERE LIVE PASS”. În lipsa probelor trecem `BLOCKED`, nu publicăm.

## Etapa 0 — Inventar și fezabilitate (înainte de dezvoltare)

**Acțiuni**
1. Inventariază toate importurile, executabilele, shell calls, căile `D:\AI-Video-Editor`, parserele Python și referințele la motorul 01 din pipeline-ul 00/02/03/04.
2. Extrage contractele MOGRT aprobate: șablon, versiune, fonturi, toate câmpurile editable, poziționare track, readback și cerințele de render; verifică dacă funcționează pe un Premiere cu numai Adobe/Premiere (fără After Effects, font activat cloud sau efecte externe).
3. Verifică exact versiunile Premiere vizate: 25.0–25.5, 25.6, cea mai recentă versiune; macOS Intel și Apple Silicon dacă sunt suportate de versiunea Adobe.
4. Prototip minimal UXP pe 25.6+ pentru import MOGRT și modificarea + citirea parametrilor **text + Bold Words + Orange**. Încadrează fiecare API ca `SUPPORTED`, `PARTIAL` sau `BLOCKED`; nu activa UXP în versiunea utilizatorului dacă nu trece probele.
5. Auditează pachetul vechi Stable R1.9.13, canalele de update și conflictul de ID între Stable/Beta.

**Livrabil:** `docs/stable/COMPATIBILITY_MATRIX_RO.md` + listă dependențe eliminate + contract JSON de adaptare.
**GATE 0:** confirmarea fezabilității MOGRT reale pe Mac și Windows; dacă UXP este incomplet, strategia CEP pe hosturile compatibile rămâne temporară, fără promisiuni post-2029.

## Etapa 1 — Motor DOCX pur JavaScript (offline)

**Acțiuni**
1. Extrage regulile validate ale readerului R2.3.7 într-un pachet independent de Adobe/OS.
2. Include ZIP/XML parser licențiat, fără apeluri externe și cu controale anti zip-bomb. Mapare OOXML: `w:p`, tabel 2/6 coloane, celule unite, cod sursă, TC, `SINCRON`, `AMB`, `CN`, uppercase VO, nume+funcție, Italic/Regular, Strikethrough.
3. Asigură verificarea de acoperire editorială: pentru fiecare pasaj DOCX eligibil -> `V3`, `V4`, `V5`, `SKIP_EXPLICIT` sau `REVIEW`, cu referință stabilă de paragraf/bloc; zero omisiuni silențioase.
4. Pregătește un plan JSON imutabil: `docSha256`, `parserVersion`, `blocks`, `coverage`, `warnings`, `timingMode`, `targetTrack`; schemă versionată compatibilă cu ambele adaptoare.
5. Golden tests pe matricea de formate: Casa Angelus (VASILE ≠ subtitrare), Muncitori (Italic/Regular mixt), Satul Nou (GEO), Cernobîl (sursă la început), Veterinar (SINCRON inline), Balatina (0012, VO, 6 NameTag), Bubuieci, tabel șase coloane, strikethrough și Unicode. Date private nu sunt puse în repo.

**Livrabil:** `packages/editorial-core/`, `tests/golden/` cu fișiere sintetice, raport diferențe față de analiza existentă.
**GATE 1:** toate fixture-urile trec; rezultatul de acoperire DOCX este integral sau are `REVIEW` explicit. Zero Python/ASR/shell în runtime.

## Etapa 2 — Panel CEP autonom și executor Premiere

**Acțiuni**
1. Creează extensia cu ID separat de Beta, UI simplificat la cinci secțiuni, fonturi/locații configurate portabil.
2. Integrează `editorial-core` în panou fără `exec`/CLI; DOCX din file-picker Windows/Mac; cache per SHA.
3. Integrează executorul MOGRT aprobat fără refactor distructiv: `V3` text EXACT, `V4` identități, `V5` cartoane; MOGRT-urile și orice librărie necesară sunt incluse legal în pachet.
4. Distinge `SCRIPT_PREVIEW` de `SYNCED`: dacă nu există ancore audio/marker validate și modulul 01 nu este inclus, utilizatorul primește preview și o explicație clară, nu sincronizare inventată.
5. Păstrează verificarea pistei înainte și după, collision/lock, readback real, confirmare la operațiuni destructive, iar la eroare STOP fără afectarea materialelor existente.
6. Testează 16:9 și 9:16; V5 preferabil 28/maximum 29 caractere/rând, 4 rânduri/pagină și accente Orange/Bold identice.

**Livrabil:** primă extensie **Portable Candidate** CEP (fără publicare Stable).
**GATE 2:** Premiere LIVE pe Windows cu DOCX nou și secvențe curate/ocupate; readback 00/02/03/04, Unicode, piste neschimbate, nicio dependență `D:\AI-Video-Editor`.

## Etapa 3 — Instalare privată Windows + Mac și updater

**Acțiuni**
1. Pregătește ZXP semnat pentru CEP, cu test pe instalări Premiere/Creative Cloud curate pe Windows și macOS; verifică font/MOGRT, Intel/Apple Silicon, permisiuni file-picker și căi Unicode.
2. Creează canalul **Stable Autonomous** separat de Beta: repository privat sau distribuție internă cu drepturi explicite de citire; fluxul de autentificare pentru update **nu** poate pune PAT-uri în plugin.
3. Build CI semnat, manifest Ed25519 și SHA-256; versioning semver, allowlist de fișiere, compatibilitate OS/Premiere, downgrade controlat, rollback prin reinstalarea pachetului anterior valid.
4. Buton „Verifică actualizările” -> descarcă pachetul în spațiu temporar -> verifică semnătura, SHA și compatibilitatea -> deschide instalarea prin mecanismul Adobe; nu edita direct un ZXP instalat. Fără acces internet în restul extensiei.
5. Testează: fără conexiune, release lipsă, release neautorizat, SHA/semnătură incorectă, update întrerupt, instalare eșuată, rollback, două versiuni separate Beta/Stable.

**Livrabil:** ZXP intern distribuibil, updater funcțional cu rollback și document scurt de instalare pentru colegi.
**GATE 3:** instalare/actualizare/rollback LIVE reușite pe Windows și Mac fără instrumente de dezvoltare sau dependențe suplimentare la utilizator.

## Etapa 4 — UXP și compatibilitate viitoare

**Acțiuni**
1. Creează adapter UXP care folosește **același** `editorial-core`, fără duplicarea regulilor.
2. Gate de import/editare/readback MOGRT text, Italic/Regular, NameTag două câmpuri, V5 Orange/Bold, collision și rollback. Dacă API-urile nu permit rezultatul aprobat, păstrează adapterul UXP în `BLOCKED`, nu promova pluginul.
3. Când trece probele, livrează CCX separat, instalabil prin Creative Cloud Desktop și testat pe Mac/Windows și Premiere 25.6+. Arhitectura permite ieșirea din CEP înainte de eliminarea sa.
4. Politica „2025+” se menține drept obiectiv pe termen lung, dar compatibilitatea fiecărei versiuni de Premiere este certificată în matrice; nu promite 2030+ fără UXP operațional.

**Livrabil:** `adapter-uxp/` și CCX intern după validarea MOGRT.
**GATE 4:** Premiere UXP LIVE PASS, inclusiv panou și trei module MOGRT. Fără acest gate, livrarea imediată este CEP doar pentru hosturile compatibile.

## Etapa 5 — Lansare controlată Stable

**Acțiuni**
1. QA cu scenarii reale pe copii de secvență, Mac + Windows, 16:9 + 9:16, offline și fără căi/dependențe dezvoltator.
2. Pilot intern cu colegii (niciun DOCX transmis în afara dispozitivului).
3. Rulează matricea de regresie, inclusiv upgrade/rollback și coexistența Beta.
4. Numai după `PREMIERE LIVE PASS` pe platformele declarate: aprobare și promovare a noului canal Stable. **Nu suprascrie R1.9.13 fără backup și validare.**

**Livrabil:** versiune Stable Autonomous semnată, note pentru echipă, instrucțiune scurtă și registru de compatibilitate reală.

## Registru de riscuri / decizii

| Risc | Măsură | Stare |
|---|---|---|
| CEP dispare din Premiere după noiembrie 2029 | Core JS comun + adapter UXP, gate înainte de lansare | DESCHIS |
| Text MOGRT pe UXP incomplet în 2026 | Prototip API și fallback temporar CEP compatibil | DESCHIS |
| MOGRT dependent de After Effects/font/plugin | Audit pe macOS și Windows curate, reproiectare șablon dacă este necesar | DESCHIS |
| Update privat necesită autentificare | Repository privat / acces autorizat fără PAT în client; verificare criptografică | DE DECIS TEHNIC |
| Instalare ZXP/CCX diferă între OS | Folosim installer Adobe, testăm ambele OS | DESCHIS |
| Preview confundat cu sincronizare | Indicator permanent și gate de ancore verificate | CONTROL CONTRACTUAL |
| Modificare Beta / Stable vechi | Branch izolat și niciun release până la acceptare | PROTEJAT |

## Următoarea acțiune autorizată

Această rundă livrează **numai cele două documente** în `feature/stable-autonomous-crossplatform-spec`. Nu pornește implementarea, nu publică release, nu schimbă workflow-uri, Beta, Stable R1.9.13 și nici directoare Premiere. **Primul pas efectiv după aprobarea planului** este inventarul tehnic Etapa 0 și o matrice compatibilitate MOGRT Windows/macOS, fără schimbări în produsele instalate.


## Amendament 2026-11-02: instituție IT-managed, fără instalare liberă de aplicații
**Prioritate nouă înainte de Etapa 0:** audit de distribuție pe două stații administrate, cu acceptul IT. Mac are Premiere 2026, Windows are atât Premiere 2025 cât și 2026. După instalarea prin Extensions/Creative Cloud, pluginurile existente rulează. Nu confunda asta cu dreptul de a instala orice CCX/ZXP nou.

**Etapa 0A — Poarta IT (fără executabile ori modificări de sisteme):**
1. Identifică versiunile complete `25.x`, `26.x` și Adobe ID/planul administrat — mai ales dacă echipa folosește Adobe Admin Console Enterprise/Teams sau Creative Cloud individual gestionat de IT.
2. Confirmă cu IT metoda acceptată: plugin Marketplace self-service, CCX intern prin Creative Cloud Desktop, ori distribuție privată prin Adobe Admin Console Managed Package/UPIA; solicită aprobare pentru URL-ul de updates doar la click.
3. Definim permisiuni minime `localFileSystem: request` plus sandbox, fără fullAccess/native helper/Developer Mode la utilizatori. Prezentăm IT un pachet de analiză cu lista permisiunilor, surse cod, hash, licențe și politica de date offline.
4. Pilot pe un Mac Premiere 26 și un Windows Premiere 25.6+/26 cu `UXP .ccx` **NUMAI după probe reale MOGRT**. Pentru 25.0–25.5: `CEP .zxp` autorizat, dacă instanța o cere; niciun instrument de dezvoltare pe stațiile monitorizate.
5. Dacă IT interzice actualizările direct, butonul Actualizări numai verifică/distribuie informații; instalarea/rollback se face exclusiv prin Creative Cloud/IT. Nu încerca scriere în directoarele pluginurilor sau UPIA fără aprobare.

**GATE IT:** administratorul confirmă canalul acceptat și permisiunile; pachetul nu necesită instalarea altui software; după instalare 00/02/03/04 rulează offline. Dacă Adobe Premiere 26 UXP nu poate modifica toate câmpurile MOGRT, testul devine `BLOCKED` și se păstrează arhitectura duală până la disponibilitatea oficială API. Fără publicare Marketplace publică implicit.

**Notă de risc:** un CCX obișnuit este instalabil prin Creative Cloud Desktop, dar anumite permisiuni și politici organizaționale pot solicita admin. Un plugin UXP Hybrid cu native code ar solicita admin și este **exclus**. Dezvoltarea folosind UXP Developer Tool are nevoie de admin pe calculatorul de dezvoltare, NU pe stațiile utilizatorilor.
