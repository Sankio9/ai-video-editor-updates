# R2.3.0 — Învățare DOCX și module independente (30 octombrie 2026)

## Regula aprobată
02 Subtitrări, 03 NameTag și 04 Cartoane VO trebuie să funcționeze **fiecare independent**, inclusiv pe o secvență Premiere fără montaj pe V1/A1, pentru DOCX nou încărcat în 00. Modul independent nu cere surse din Project Panel, ASR, timecode-uri sau raport R143/R220. Nu pretinde sincronizare audio: 02 este `SCRIPT_PREVIEW`, 03/04 `EDITORIAL_PREVIEW`. MOGRT, pistele V3/V4/V5, preflight, verificările de coliziune, protecția la suprascriere și rollback rămân identice cu executorul aprobat.

## Formate recunoscute (din nouă DOCX reale, analizate local; fișierele personale NU sunt publicate în repository)
- Reportaj nativ: fraze uppercase în casete VO, coduri 4 cifre, timp `1.14` / `00.12`, nume și funcție în paragrafe separate, ambianță și GEO
- Reportaj VOX: antete `VOX` / `SINCRON: NUME, funcție`, coduri sursă, declarații cu timecode
- Interviu documentar: `SINCRON`, `C9625`, `CARTON:` și `AMBIANȚĂ` într-un paragraf sau pe paragrafe diferite, 1–3 timecode-uri
- Video redacțional internațional: `PKG`, `SOT [07:08]`, nume/funcție pe linii, cartoane uppercase, speaker fără cod
- Format tabular: două coloane sursă/B-roll și declarații, celule Word unite; nu dubla celulele unite și nu transforma automat textul de narator într-un carton pe ecran
- Sursa/regie: `GEO`, surse media, URL-uri, credits, online/duration/title/intro; nu trebuie confundate cu subtitrare ori burtieră
- Clip cu SOT fără nume/titlu valid: subtitrarea replicii se poate crea, dar burtiera NU trebuie inventată

## Algoritmul
1. Reader conservator al paragrafelor și tabelelor DOCX în ordine reală; extrage doar text identificabil. Recunoaște coduri sursă standalone și `C9625`, IN/OUT `mm:ss` sau `m.ss`, implicit fără obligativitatea lor.
2. 02: numai replicile/declarațiile, nu descrierile de imagine sau cartoanele. Textul se împarte prin algoritmul aprobat de maxim 74 caractere și nu rupe cuvinte. Bifa Strikethrough elimină fragmentele tăiate pentru formatele suportate; scripturile vechi folosesc în continuare parserul aprobat.
3. 03: numai identitățile explicit furnizate (nume + funcție), o burtieră pe bloc, repetate la reintroducere; identitățile insuficiente sunt în REVIEW, nu fabricate. Un DOCX fără asemenea identități poate avea zero burtiere — acesta este un rezultat editorial corect.
4. 04: `CARTON:` / `CARTON FINAL:` sau texte editoriale uppercase; ignoră meta, GEO, surse și ambient. Layout/paginarea deja aprobată se aplică pe 4 linii × maxim 33 caractere, Orange + Bold Words.
5. Păstrează `r20_graphics_plans.build` aprobat drept rută principală pentru formatul deja recunoscut. Apelează `r230_universal.build` numai la erorile `Nu am identificat declarații în DOCX` și `Nu există cartoane editoriale în DOCX`. Restul erorilor legacy rămân STOP. Fără modificări la writerul JSX.
6. Dacă un modul nu are date explicite corespunzătoare, raportează clar `Nu sunt declarații`, `Nicio burtieră validă` sau `Nu există cartoane` — fără a altera timeline-ul.

## Dovezi și limite de acceptare
- Analiză/parsing local pe toate cele nouă DOCX ale utilizatorului: PASS, inclusiv un document construit aproape integral ca tabel și documente cu strikethrough. Unele fișiere nu conțin identități sau cartoane explicite; modul respectiv nu fabrică output.
- Build plan pentru 02/03/04 verificat pe cele nouă DOCX în mediu local cu splitter/layout simulat: PASS; nu reprezintă testul real al rendererului MOGRT.
- GitHub CI `41018003189` și `41018278152` SUCCESS: generatorul SHA-pinned din release R2.1.2 cu fallback R2.3, opt formate DOCX sintetice, rezultat strict pe două fișiere.
- Release `v2.3.0` Beta, asset `AIVE_UPDATE.zip`, SHA256 `34a824f71d228d7b45a72314d1a6a3c6edf227081be976c7a608d4f3a246d6af`.
- **LIVE în Premiere Pro 2025 este încă NEVALIDAT**. CI nu confirmă inserarea reală MOGRT. Stable R1.9.13 rămâne protejată. Nu solicita repetarea testelor istorice pentru R220; testul actual se referă exclusiv la 02/03/04 Independent cu un DOCX și pistele destinație.

## Pentru următoarea etapă
Dacă un DOCX nou nu este recunoscut, colectează tiparul și eșecul concret al readerului; nu adăuga fallback pe orice eroare și nu elimina SHA. Păstrează o singură încărcare DOCX în 00, câte un buton per modul și notificări clare. Extinde corpusul cu DOCX noi numai cu permisiunea editorului, fără încărcarea documentelor private în GitHub.
