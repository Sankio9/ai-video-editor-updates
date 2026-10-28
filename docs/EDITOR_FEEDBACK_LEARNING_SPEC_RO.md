# AI Video Editor — „Învață din corecturile mele” (specificație viitoare, 2026-10-28)

## Cerința utilizatorului
Un viitor buton unic **„Compară cu editarea mea”** (sau „Învață din corecturile mele”) va inspecta în modul READ-ONLY timeline-ul Premiere, va compara ceea ce a generat AI Video Editor cu ceea ce editorul a modificat manual și va prezenta diferențe concrete, **pentru aprobare editorială înainte de adoptarea regulilor**. Scop: îmbunătățire progresivă a segmentării subtitrărilor, duratelor, NameTag-urilor, cartoanelor și ulterior a montajului.

**Nu se implementează acest buton în R2.1.2** (utilizatorul l-a cerut pentru viitor). Nu confunda aprobarea acestei specificații cu aprobarea automată a regulilor rezultate.

## Etape obligatorii

1. **Snapshot înainte**: salvează la fiecare generare un registru local, fără date în public GitHub: SHA-256 DOCX, versiunea generatorului, Project/Sequence identity, formatul 9:16/16:9, track, MOGRT template, id stabil `R20-*`, group/CUT, text exact, delimitările, start/end/durată, stil și parametri verificabili. Include SHA pentru plan și manifest. Dacă extensia nu deține metadate suficiente pentru o asociere sigură, marchează `REVIEW_IDENTITY`, nu inventa un match.
2. **Snapshot după**: citește, fără modificare, pista activă din Premiere: ordinea MOGRT-urilor, text (numai dacă readback Adobe permite efectiv), start/end/durată, stiluri/transformări compatibile, blocuri eliminate/adăugate, numele MOGRT. Metoda de citire pentru text trebuie validată în PREMIERE LIVE; nu presupune că toate proprietățile MOGRT pot fi inspectate.
3. **Compară**: aliniere 1:1 după identitate verificată; apoi read-only candidates pentru cazuri multiple sau editări împărțite/fuzionate. Evidențiază text șters/adăugat, granițe de subtitrare mutate, durată diferită, stilul schimbat, ordinea alterată și identificările schimbate. Nu interpretează orice modificare ca regulă bună.
4. **Propune**: grupează exemple repetate în propuneri de regulă descrise în română (ex. „Echilibrează două subtitrări de 71/15 la 43/43”), cu cazurile înainte/după, costuri, excepții și risc. Prioritizează dovezi din mai multe editări; o singură corectură nu devine automat lege globală.
5. **Aprobare**: pentru FIECARE propunere, utilizatorul poate **Aprobă / Respinge / Amână**. Fără aprobare explicită nu se schimbă nicio regulă, cod, MOGRT sau clip existent.
6. **Aplicare controlată**: transformarea regulii aprobate în patch este o operațiune separată, testată pe exemplele aprobate + regresiile existente; numai apoi se propune Beta. Cu fiecare regulă: ID, explicație, data aprobării, dovezi, teste, versiune, rollback și control de dezactivare.
7. **Confidențialitate**: transcriptul și textul editorului rămân local în `D:\AI-Video-Editor\Temp\Learning\` cu retenție limitată și purge explicit. Niciun clip, DOCX, nume/identitate de intervievat sau transcript nu se publică automat în repository sau servicii externe.

## Constrângeri de siguranță

- Citirea unei secvențe existente nu cere și nu execută write/overwrite pe V1/A1/V3/V4/V5. Nicio operație destructive/QE API pentru creare de piste.
- Nu scanează sau nu compară automat proiecte care nu au istoric/plan de generare valid. Diferențele ambiguë se raportează distinct, fără a „învăța” greșit.
- Se poate compara aceeași sursă cu alte cuturi/track positions doar cu identitate confirmată; nu deduce corectitudinea dintr-o coincidență de timestamp.
- Regulile aprobate pentru 02 Subtitle nu se aplică automat altor module.
- Un model local poate ajuta la categorisirea **propunerilor**, dar nu are autoritate să insereze text sau să învețe dintr-un exemplu fără confirmare. Soluția poate fi complet locală/zero-cost cu diffs deterministe înaintea unui model de limbaj.
- Teste de acceptare: **zero writes la scanare**, matched/unmatched/ambiguous corect, diffs text/timing/layout, aprobarea editorială separat de commit, regresii și rollback. Necesită probă Adobe Premiere LIVE că citirea textului în MOGRT este suportată înainte de implementarea UI publică.

## Exemplu de regulă de învățat

AI a produs două subtitrări dintr-o singură frază: prima 70 de caractere, a doua 15. Editorul le-a împărțit în 41 și 34. Comparatorul arată ambele variante, evidențiază doar locul rupturii și propune „Păstrează delimitările naturale, echilibrează fragmentele fără resturi”. Această regulă va fi activată doar după aprobare și teste; se păstrează excepția pentru o propoziție scurtă independentă.

## Prioritate

1. Finalizează R2.1.2 Beta — segmentare echilibrată V3 și test LIVE.
2. Finalizează Montaj 01 fail-closed 8/17 și Sync 02.
3. Construiește **snapshot generator + timeline read-only**, apoi comparatorul și interfața de aprobare într-un release Beta separat. Nu grăbi acest buton în Stable.
