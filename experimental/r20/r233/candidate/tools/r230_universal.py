from __future__ import annotations
import re, hashlib, json
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
MARK = re.compile('^(SINCRON|VOX|SOT|CARTON(?: FINAL)?|AMBIAN[TȚ]Ă|AMB|PKG)\\b\\s*[:–—-]?\\s*(.*)$', re.I | re.S)
META = re.compile('^(?:TITLU|INTRO|AUTOR(?:I)?|DURATION|SOURCE|SURSA|SURSĂ|GEO|GEIO|ONLINE|CLEAN|FTP|VIDEO SERVER|ON SERVER|SERVER LOCATION|PANGEA LINK|SCRIPT|RFE/RL|REUTERS|B-ROLL|FACEBOOK|X\\s*[-:]|https?://|\\\\\\\\)', re.I)
CODE = re.compile('^(?:[Cc]\\d{4}|\\d{4})$')
TIMECODE = re.compile('(?<!\\d)(?:\\d{1,2}[:.]\\d{2})(?!\\d)')
TIMECODE_ONLY = re.compile('^[\\s\\[\\]()–—-]*(?:\\d{1,2}[:.]\\d{2}[\\s\\[\\]()–—-]*){1,3}$')
PERSON = re.compile('^[A-ZĂÂÎȘȚ][\\wăâîșțĂÂÎȘȚ\\-]+(?:\\s+[A-ZĂÂÎȘȚ][\\wăâîșțĂÂÎȘȚ\\-]+){0,4}$', re.U)
BARRIER = re.compile('^(?:GEO|SURS[ĂA]|SOURCE|AMB|AMBIAN[TȚ]Ă|PKG|SOT|SINCRON|VOX|CARTON)\\b', re.I)

def clean(s):
    return re.sub('\\s+', ' ', s.replace('\xa0', ' ')).strip()

def isupper(s):
    letters = [c for c in s if c.isalpha()]
    return len(letters) >= 9 and sum((c.isupper() for c in letters)) / len(letters) > 0.88

def paragraphs(doc):
    """Yield Word paragraphs and RIGHT-hand table paragraphs including
    rows whose LEFT cell is empty. Do not repeat merged cells.
    """
    for block in doc.element.body.iterchildren():
        if block.tag == qn('w:p'):
            yield Paragraph(block, doc), None
        elif block.tag == qn('w:tbl'):
            table = Table(block, doc)
            for row in table.rows:
                cells,seen = [],set()
                for cell in row.cells:
                    key=id(cell._tc)
                    if key not in seen:
                        seen.add(key)
                        cells.append(cell)
                if len(cells) < 2 or cells[0]._tc is cells[-1]._tc:
                    continue
                left,right=cells[0],cells[-1]
                for p in right.paragraphs:
                    if clean(p.text):
                        yield p,left.text

def styled_parts(paragraph):
    """Group consecutive Word runs by italic style, never across a style
    boundary. Also preserve independent Strikethrough per fragment.
    """
    parts=[]
    for run in paragraph.runs:
        raw=run.text or ''
        if not raw:
            continue
        inherited=(run.style.font.italic if run.style else None)
        paragraph_italic=(paragraph.style.font.italic if paragraph.style else None)
        italic=(run.italic is True or
                (run.italic is None and (inherited is True or paragraph_italic is True)))
        crossed=run.font.strike is True or run.font.double_strike is True
        if parts and parts[-1]['italic']==bool(italic):
            parts[-1]['text']+=raw
            if not crossed:
                parts[-1]['filtered']+=raw
        else:
            parts.append({'text':raw,'filtered':'' if crossed else raw,
                          'italic':bool(italic)})
    if not parts and paragraph.text:
        parts=[{'text':paragraph.text,'filtered':paragraph.text,
                'italic':bool(paragraph.style and paragraph.style.font.italic)}]
    return [p for p in parts if clean(p['text'])]

def splitlines(text):
    return [clean(x) for x in text.splitlines() if clean(x)]

def strip_tc(text):
    lines = splitlines(text)
    out = []
    for line in lines:
        if TIMECODE_ONLY.fullmatch(line) or CODE.fullmatch(line):
            continue
        line = re.sub('^\\s*\\d{1,2}[:.]\\d{2}(?:\\s*[-–—]\\s*\\d{1,2}[:.]\\d{2})?\\s*', '', line)
        line = re.sub('\\s+\\d{1,2}[:.]\\d{2}\\s*$', '', line)
        if clean(line):
            out.append(clean(line))
    return clean(' '.join(out))

def split_identity(text):
    s = clean(text).strip(',')
    if not s or len(s) > 110 or re.search('\\d', s):
        return None
    parts = s.split(',', 1)
    name = parts[0].strip()
    if len(name) > 52 or len(name.split()) > 5 or (not name):
        return None
    if not (PERSON.fullmatch(name) or (name == name.upper() and len(name) < 38 and (len(name.split()) <= 3))):
        return None
    role = clean(parts[1]) if len(parts) > 1 else ''
    if role and (not looks_role(role)):
        return None
    return (name, role)

def looks_role(s):
    t = clean(s)
    if not t or len(t) > 100 or any((t.endswith(x) for x in '.!?')):
        return False
    return bool(re.search('(?i)^(?:primar|locuitor|locuitoare|farmacist|asistent|student|pensionar|mam[ăa]|fiic[ăa]|deputat|sociolog|șef|sef|angajat|activist|reporter|profesor|președinte|presedinte|director|reprezentant|corpul|ofițer|soldat|militar)', t))

def paragraph_rows(doc):
    rows=[]
    for p,left in paragraphs(doc):
        raw=p.text
        if not clean(raw):
            rows.append({'text':'','idx':len(rows),'blank':True,'table':False,
                         'bold':False,'strike':False})
            continue
        runs=styled_parts(p)
        filtered=''.join(part['filtered'] for part in runs)
        thick=sum(len(r.text) for r in p.runs if r.bold or
                  (r.style and 'bold' in r.style.name.lower()))
        rows.append({'text':clean(raw),'raw':raw,'idx':len(rows),
            'table':left is not None,'left':left or '','parts':runs,
            'bold':thick/max(1,len(raw))>0.45,
            'italic':all(part['italic'] for part in runs),
            'strike':filtered!=raw,'without_strike':clean(filtered)})
    return rows

def parse(docx):
    docx = Path(docx)
    rows = paragraph_rows(Document(docx))
    events = []
    cards = []
    segments = []
    warnings = []
    section = False
    in_explicit = False
    sync_active = False
    carton = []
    carton_start = 0
    who = None
    title = ''
    src = None
    source_i = None
    last_identity = None
    block = 0
    uppercase = []
    uppercase_i = 0

    def flush_card():
        nonlocal carton, last_identity, who, title, src, sync_active
        text = clean(' '.join(carton))
        if text:
            cards.append({'text': text, 'paragraph': carton_start, 'kind': 'explicit'})
            last_identity = None
            who = None
            title = ''
            src = None
            sync_active = False
        carton = []

    def flush_upper():
        nonlocal uppercase, last_identity, who, title, src, sync_active
        text = clean(' '.join(uppercase))
        if text:
            cards.append({'text': text, 'paragraph': uppercase_i, 'kind': 'uppercase'})
            last_identity = None
            who = None
            title = ''
            src = None
            sync_active = False
        uppercase = []

    def voice(text, i, kind='interview', raw=None, filtered=None, italic=False):
        nonlocal block,last_identity
        text=strip_tc(text)
        if not text or len(text)<2:
            return
        reporter=bool(italic) or kind=='narration'
        ident=(None,None,None) if reporter else (who,title,src)
        if ident!=last_identity:
            block+=1
        last_identity=ident
        segments.append({'ordinal':len(segments)+1,'paragraph_start':i,
            'paragraph_end':i,'source_code':ident[2],
            'speaker':ident[0],'role':ident[1],
            'text':text,'block':block,'reporter_italic':reporter,
            'kind':'narration' if reporter else kind,
            'raw':raw if raw is not None else text,
            'text_without_strike':strip_tc(filtered) if filtered is not None else text})

    def voice_parts(row,i,kind='interview',force_italic=None):
        parts=row.get('parts') or [{'text':row.get('raw',row['text']),
            'filtered':row.get('without_strike',row['text']),
            'italic':row.get('italic',False)}]
        if force_italic is not None:
            text=''.join(p['text'] for p in parts)
            filtered=''.join(p['filtered'] for p in parts)
            voice(text,i,kind='narration' if force_italic else kind,
                  raw=text,filtered=filtered,italic=force_italic)
        else:
            for p in parts:
                voice(p['text'],i,kind=kind,raw=p['text'],
                      filtered=p['filtered'],italic=p['italic'])
    j = 0
    while j < len(rows):
        r = rows[j]
        s = r['text']
        i = r['idx']
        j += 1
        if not s:
            flush_upper()
            continue
        if r.get('table'):
            flush_upper()
            flush_card()
            section=True
            labels=splitlines(r['left'])
            named=split_identity(labels[0]) if labels else None
            verified=bool(named and (named[1] or
                          (len(labels)>1 and looks_role(labels[1]))))
            if verified:
                who=named[0]
                title=named[1] or clean(labels[1])
                src=None
                sync_active=True
                voice_parts(r,i,kind='table_sot')
            elif r.get('bold'):
                # Bold text is a possible SOT but lacks a confirmed NameTag.
                who=None
                title=''
                src=None
                last_identity=None
                sync_active=True
                voice_parts(r,i,kind='table_sot',force_italic=False)
            else:
                # Ordinary right-column text beneath GEO/source/B-roll is CN.
                who=None
                title=''
                src=None
                last_identity=None
                sync_active=False
                voice_parts(r,i,kind='narration',force_italic=True)
            continue
        if s.lower() in ('script:', 'script', 'pkg'):
            section = True
            flush_upper()
            flush_card()
            who = None
            title = ''
            sync_active=False
            continue
        if META.match(s):
            flush_upper()
            flush_card()
            sync_active=False
            continue
        m = MARK.match(r.get('raw', s).strip())
        if m:
            label, detail = (m.group(1).upper(), m.group(2).strip())
            flush_upper()
            if label.startswith('CARTON'):
                flush_card()
                section = True
                in_explicit = True
                sync_active=False
                carton_start = i
                if detail:
                    carton.append(detail)
                continue
            flush_card()
            in_explicit = False
            section = True
            if label in ('AMBIANȚĂ', 'AMBIANTA', 'AMB', 'PKG'):
                who = None
                title = ''
                src = None
                sync_active=False
                continue
            if label in ('SINCRON', 'SOT', 'VOX'):
                src = None
                who = None
                title = ''
                last_identity = None
                sync_active=True
                payload = re.sub('\\[\\d{1,2}[:.]\\d{2}\\]', '', detail).strip()
                parts = splitlines(payload)
                person = split_identity(parts[0]) if parts else None
                if person:
                    who, title = person
                    if not title and len(parts) > 1 and looks_role(parts[1]):
                        title = parts[1]
                elif payload and (not CODE.fullmatch(payload)):
                    warnings.append({'paragraph': i, 'code': 'SPEAKER_UNCLEAR', 'text': payload[:95]})
                continue
        if in_explicit:
            carton.append(s)
            continue
        if CODE.fullmatch(s):
            flush_upper()
            src = s
            sync_active=True
            source_i = i
            look = [x for x in rows[j:j + 3] if x['text']]
            if look:
                person = split_identity(look[0]['text'])
                if person and (person[1] or (len(look) > 1 and looks_role(look[1]['text']))):
                    who = person[0]
                    title = person[1] or clean(look[1]['text'])
            continue
        if TIMECODE_ONLY.fullmatch(s):
            flush_upper()
            continue
        person = split_identity(s)
        future = [x for x in rows[j:j + 3] if x['text']]
        if person and (person[1] or (future and looks_role(future[0]['text']))) and (not isupper(s)):
            flush_upper()
            who = person[0]
            title = person[1] or (clean(future[0]['text']) if future else '')
            sync_active=True
            if not title:
                warnings.append({'paragraph': i, 'code': 'NAME_WITHOUT_ROLE', 'text': s})
            continue
        if looks_role(s) and who:
            flush_upper()
            title = s
            sync_active=True
            continue
        if isupper(s) and (not TIMECODE_ONLY.fullmatch(s)):
            nextrow = next((x for x in rows[j:j + 2] if x['text']), None)
            if len(s) < 45 and len(s.split()) <= 3 and PERSON.fullmatch(s.title()) and nextrow and (not isupper(nextrow['text']) and (not META.match(nextrow['text']))):
                flush_upper()
                who = s.title()
                title = ''
                section = True
                warnings.append({'paragraph': i, 'code': 'NAME_WITHOUT_ROLE', 'text': s})
                continue
            if uppercase and (len(s) > 65 or len(uppercase[-1]) > 65):
                flush_upper()
            if not uppercase:
                uppercase_i = i
            uppercase.append(s)
            section = True
            continue
        flush_upper()
        if not section:
            continue
        if re.match('(?i)^(?:Imagini\\b|Voice of Local\\b|Surs[ăa]\\s*[-:]|RFE/RL\\b)', s):
            continue
        if s.startswith(('http://', 'https://', '\\\\')):
            continue
        if person and len(s) < 42 and future and TIMECODE_ONLY.fullmatch(future[0]['text']):
            who = person[0]
            title = person[1]
            sync_active=True
            continue
        if not sync_active and not who and not src:
            # CN written as ordinary paragraphs (not only two-column tables)
            # is narrator voice, not an anonymous interviewee.
            voice_parts(r,i,kind='narration',force_italic=True)
        else:
            voice_parts(r,i,kind='interview')
    flush_upper()
    flush_card()
    # No explicit cue in the DOCX. A plain editorial transcript with several
    # complete sentences may still be valid CN, but metadata, headlines,
    # credits and isolated cards cannot silently become interview material.
    if not segments and not cards:
        candidates=[]
        for r in rows:
            txt=clean(r.get('text',''))
            if (not txt or r.get('table') or META.match(txt) or
                MARK.match(txt) or CODE.fullmatch(txt) or
                TIMECODE_ONLY.fullmatch(txt) or isupper(txt)):
                continue
            if (len(txt)>=45 and len(txt.split())>=7 and
                re.search(r'[.!?…]',txt) and
                not re.match(r'(?i)^(?:http|www\.|titlu|autor|durat|data|copyright|fotograf)',txt)):
                candidates.append(r)
        # One sentence can be the article teaser. Require at least two
        # distinct narrative paragraphs to activate automatic CN preview.
        if len(candidates)>=2:
            for r in candidates[1:]:
                txt=strip_tc(r['text'])
                if not txt:
                    continue
                block+=1
                segments.append({'ordinal':len(segments)+1,
                    'paragraph_start':r['idx'],'paragraph_end':r['idx'],
                    'source_code':None,'speaker':None,'role':None,'text':txt,
                    'block':block,'reporter_italic':True,'kind':'auto_cn',
                    'raw':r['text'],
                    'text_without_strike':strip_tc(r.get('without_strike',r['text']))})
            warnings.append({'code':'AUTO_CN_PLAIN_SCRIPT_REVIEW',
                'paragraph':candidates[1]['idx'],
                'text':'Text fără marcaje: previzualizare narator Italic, nu sincron audio.'})
    return {'segments': segments, 'captions': cards, 'warnings': warnings,
            'rows': rows, 'source': docx.name}

def duration(text, minimum=1.15, maximum=8.0, cps=14):
    return round(min(maximum, max(minimum, 0.6 + len(text) / cps)), 3)

def build(docx, module, separator=0.75, omit_struck=False):
    from r20_graphics_plans import split_subtitles_readable
    from r204_carton_layout import build_pages
    docx = Path(docx).resolve()
    if not docx.exists() or docx.suffix.lower() != '.docx':
        raise ValueError('DOCX invalid / lipsă')
    if module not in ('02', '03', '04'):
        raise ValueError('Modul invalid')
    if not 0 <= separator <= 2:
        raise ValueError('Separator invalid')
    if type(omit_struck) != bool:
        raise ValueError('Strikethrough trebuie boolean')
    parsed = parse(docx)
    items = []
    skipped = []
    audit = []
    count = 0
    cursor = 0.0
    groupcount = set()

    def add(group, text, seconds, more):
        nonlocal cursor, count
        if not text.strip():
            return
        if items and items[-1]['groupId'] != group:
            cursor += separator
        count += 1
        cursor = round(cursor, 3)
        item = {'id': 'R20-%s-%04d' % (module, count), 'groupId': group, 'text': text, 'startSeconds': cursor, 'durationSeconds': seconds}
        item.update(more)
        items.append(item)
        groupcount.add(group)
        cursor = round(cursor + seconds, 3)
    if module == '02':
        for seg in parsed['segments']:
            before = clean(seg['text'])
            after = clean(seg['text_without_strike']) if omit_struck else before
            if before != after:
                audit.append({'cutId': 'CUT-%02d' % seg['ordinal'], 'paragraph': seg['paragraph_start'], 'before': before, 'after': after})
            if not after:
                continue
            pieces = split_subtitles_readable(after, 74)
            if clean(' '.join(pieces)) != after:
                raise ValueError('SUBTITLE_TEXT_LOSS')
            for part in pieces:
                add('CUT-%02d' % seg['ordinal'], part, duration(part, 0.9, 6.0, 13), {'fontStyle': 'Italic' if seg['reporter_italic'] else 'Regular', 'sourceParagraph': seg['paragraph_start']})
    elif module == '03':
        emitted = set()
        for seg in parsed['segments']:
            name = seg['speaker']
            title = seg['role']
            block = seg['block']
            if not name or not title:
                if seg['reporter_italic'] or seg['kind']=='narration':
                    skipped.append({'paragraph':seg['paragraph_start'],
                        'cutId':'CUT-%02d'%seg['ordinal'],
                        'sourceCode':None,'kind':'SKIP_NARRATION',
                        'reason':'Reporter/CN: fără NameTag.'})
                else:
                    skipped.append({'paragraph':seg['paragraph_start'],
                        'cutId':'CUT-%02d'%seg['ordinal'],
                        'sourceCode':seg['source_code'],
                        'kind':'REVIEW_MISSING_IDENTITY',
                        'reason':'Nume și funcție necesare; nu inventăm identificarea.'})
                continue
            if block in emitted:
                continue
            emitted.add(block)
            add('BLOCK-' + str(block), name, duration(name + ' ' + title, 3.3, 5.5, 16), {'name': name, 'title': title, 'anonymous': False, 'sourceParagraph': seg['paragraph_start']})
    else:
        for k, cap in enumerate(parsed['captions']):
            original = clean(cap['text'])
            pages = build_pages(original)
            if not pages or clean(' '.join((x['text'] for x in pages))) != original:
                raise ValueError('CARTON_TEXT_LOSS bloc ' + str(k + 1))
            for pageno, page in enumerate(pages):
                raw = page['text']
                lines = page['physicalLines']
                add('VO-' + str(k + 1), raw, duration(raw, 3.0, 9.0, 13.5), {'physicalLines': lines, 'textLine0': lines[0], 'textLines123': '\r'.join(lines[1:]), 'boldWords': page['boldWords'], 'emphasisPhrases': page['emphasisPhrases'], 'colorScheme': 'Orange', 'sourceParagraph': cap['paragraph'], 'page': pageno + 1, 'pageCount': len(pages)})
    # Zero output is not a crash and never an instruction to touch Premiere.
    # The CEP must display a clear NOT APPLICABLE message and skip the JSX
    # writer entirely. Preserve the original plan/metadata integrity checks.
    summary={'paragraphs':sum(1 for r in parsed['rows'] if r.get('text')),
             'tables':sum(1 for r in parsed['rows'] if r.get('table')),
             'speech':len(parsed['segments']),'cartons':len(parsed['captions']),
             'identified':sum(1 for seg in parsed['segments']
                              if seg.get('speaker') and seg.get('role')),
             'warnings':len(parsed['warnings'])}
    if not items:
        summary['message']=('Nu există nume și funcții explicite pentru NameTag.'
             if module=='03' else 'Nu există cartoane explicite/uppercase.'
             if module=='04' else 'Nu sunt declarații identificabile pentru subtitrare.')
    else:
        summary['message']='Material editorial identificat.'
    return {'schema': 'aive-r20-graphics-v1', 'module': module, 'mode': 'independent', 'timing': 'SCRIPT_PREVIEW' if module == '02' else 'EDITORIAL_PREVIEW', 'docx_sha256': hashlib.sha256(docx.read_bytes()).hexdigest(), 'sourceDocx': docx.name, 'separatorSeconds': separator, 'items': items, 'totalItems': len(items), 'groups': len(groupcount), 'skipped': skipped, 'reviewRequired': any((x['kind'] == 'REVIEW_MISSING_IDENTITY' for x in skipped)), 'strikePolicy': ('OMIT_STRUCK' if omit_struck else 'INCLUDE_STRUCK') if module == '02' else 'NOT_APPLICABLE', 'omittedStrikeCuts': [x['cutId'] for x in audit if not x['after']], 'removedStrikeCharacters': sum((len(x['before']) - len(x['after']) for x in audit)), 'strikeCutsChanged': len(audit), 'strikeAudit': audit, 'strikeAnalysisReady': module == '02', 'reviewPolicy': ('EXPLICIT_SKIP_APPROVAL' if any(x['kind']=='REVIEW_MISSING_IDENTITY' for x in skipped) else 'AUTO_AMBIENCE_SKIP' if skipped else 'NONE'), 'containsAudioSync': False, 'generatorVersion': 'R2.3-UNIVERSAL-DOCX-9-FORMATS', 'contentSummary': summary}
