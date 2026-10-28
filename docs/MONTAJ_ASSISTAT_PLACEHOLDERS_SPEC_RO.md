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
