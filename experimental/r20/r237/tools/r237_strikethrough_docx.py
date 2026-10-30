"""R237 optional montage Strikethrough: generate a READ-ONLY filtered DOCX
analysis copy, preserve original source + SHA. Never edit the user's DOCX.

Conservative version: if a complete paragraph becomes blank through filtering,
refuse automatic montage rather than silently renumber CUTs or VO blocks.
"""
from __future__ import annotations
import hashlib,json,os,re,tempfile
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
def sha(b):return hashlib.sha256(b).hexdigest()
def _crossed(run,paragraph):
    if run.font.strike is True or run.font.double_strike is True:
        return True
    if run.font.strike is False or run.font.double_strike is False:
        return False
    style=run.style.font if run.style else None
    if style and (style.strike is True or style.double_strike is True):
        return True
    try:
        para_style=paragraph.style.font if paragraph.style else None
        return bool(para_style and (para_style.strike is True or para_style.double_strike is True))
    except (AttributeError,TypeError):
        return False

def all_paragraphs(doc):
    # This traverses OOXML paragraphs both in the body and within tables
    # (including merged cells) exactly once, in document order.
    seen=set()
    for node in doc.element.body.iter():
        if node.tag!=qn('w:p'):continue
        key=id(node)
        if key in seen:continue
        seen.add(key)
        from docx.text.paragraph import Paragraph
        yield Paragraph(node,doc)

def filter_docx(original,folder):
    original=Path(original).resolve()
    if not original.is_file() or original.suffix.lower()!='.docx':
        raise ValueError('R237_DOCX_NOT_FOUND')
    b=original.read_bytes();before=sha(b)
    doc=Document(original)
    audit=[];counter=0;paragraph_index=0
    for paragraph in all_paragraphs(doc):
        original_text=paragraph.text
        removal=[]
        for run in paragraph.runs:
            if not run.text or not _crossed(run,paragraph):continue
            text=run.text
            if re.fullmatch(r'\s*[Cc]?\d{4}\s*',text):
                raise ValueError('R237_STRUCK_SOURCE_CODE: verifică manual codul sursei')
            removal.append(text)
        # Full-strike paragraphs may remove a CUT or VO event, changing
        # existing ordinal and verified audio match. Fail before Premiere.
        if removal and not ''.join(r.text for r in paragraph.runs if not _crossed(r,paragraph)).strip():
            raise ValueError('R237_STRUCK_ENTIRE_PARAGRAPH: marcaj integral; revizuiește înainte de montaj')
        for run in paragraph.runs:
            if run.text and _crossed(run,paragraph):
                run.text=''
        if removal:
            audit.append({'paragraph':paragraph_index,'removedCharacters':sum(map(len,removal)),
                          'removedFragments':len(removal)})
            counter+=sum(map(len,removal))
        paragraph_index+=1
    folder=Path(folder).resolve();folder.mkdir(parents=True,exist_ok=True)
    target=folder/('r237_strike_'+before[:24]+'.docx')
    manifest=folder/('r237_strike_'+before[:24]+'.json')
    with tempfile.NamedTemporaryFile(prefix='r237-',suffix='.docx',dir=str(folder),delete=False) as tmp:
        temp_path=Path(tmp.name)
    try:
        doc.save(temp_path)
        filtered=temp_path.read_bytes()
        if counter==0:
            # No text was struck, but checkbox remains a valid no-op policy.
            pass
        temp_path.replace(target)
    finally:
        temp_path.unlink(missing_ok=True)
    report={'schema':'aive-r237-strike-copy-v1','sourceDOCX':str(original),
            'originalSHA256':before,'filteredSHA256':sha(target.read_bytes()),
            'removedCharacters':counter,'changedParagraphs':len(audit),
            'audit':audit,'analysisDOCX':str(target)}
    manifest_tmp=manifest.with_suffix('.tmp')
    manifest_tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    manifest_tmp.replace(manifest)
    return report

def verify(source,analysis,manifest_path):
    m=json.loads(Path(manifest_path).read_text(encoding='utf8'))
    if (m.get('schema')!='aive-r237-strike-copy-v1' or
        Path(m.get('sourceDOCX','')).resolve()!=Path(source).resolve() or
        Path(m.get('analysisDOCX','')).resolve()!=Path(analysis).resolve() or
        m.get('originalSHA256')!=sha(Path(source).read_bytes()) or
        m.get('filteredSHA256')!=sha(Path(analysis).read_bytes())):
        raise ValueError('R237_STRIKE_PROVENANCE_CHANGED')
    return m
