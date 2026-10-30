"""R2.2 main entry for one-click Montage 01 (local process).

Invokes existing R1.9.13 ASR/Whisper in capture mode and returns a read-only
R2.2 plan. NEVER writes an editable Premiere plan / never modifies timeline.
"""
from __future__ import annotations
import argparse,json,os,sys,traceback
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/"tools"
sys.path.insert(0,str(TOOLS))

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--docx",type=Path,required=True)
    p.add_argument("--project-media",type=Path,required=True)
    p.add_argument("--sequence-id",required=True)
    p.add_argument("--device",default="cuda",choices=("cpu","cuda"))
    p.add_argument("--model",default="large-v3-turbo")
    p.add_argument("--omit-struck",action="store_true",
                   help="Use a temporary Word copy containing only non-struck text")
    a=p.parse_args(argv)
    try:
        if not a.docx.is_file() or a.docx.suffix.lower()!=".docx":
            raise ValueError("Selectează un DOCX valid.")
        if not a.project_media.is_file():raise ValueError("Nu găsesc inventarul Premiere.")
        media=json.loads(a.project_media.read_text("utf8"))
        if media.get("sequenceId")!=a.sequence_id:
            raise ValueError("Secvența Premiere s-a schimbat.")
        if "[AIVE TEST]" not in str(media.get("sequence","")):
            raise ValueError("Pentru test: activează o COPIE de secvență cu [AIVE TEST] în nume.")
        analysis_docx=a.docx
        if a.omit_struck:
            from r237_strikethrough_docx import filter_docx
            audit=filter_docx(a.docx,ROOT/"Temp"/"R237")
            analysis_docx=Path(audit["analysisDOCX"])
            os.environ["AIVE_R237_SOURCE_DOCX"]=str(a.docx.resolve())
            os.environ["AIVE_R237_AUDIT_PATH"]=str(
                (ROOT/"Temp"/"R237"/("r237_strike_"+audit["originalSHA256"][:24]+".json")))
        else:
            os.environ.pop("AIVE_R237_SOURCE_DOCX",None)
            os.environ.pop("AIVE_R237_AUDIT_PATH",None)
        os.environ["AIVE_R220_CAPTURE"]="1"
        os.environ["AIVE_R220_SEQUENCE_ID"]=a.sequence_id
        os.environ["AIVE_R220_MEDIA_JSON"]=str(a.project_media)
        os.environ["AIVE_R220_HOME"]=str(ROOT)
        from r220_capture import R220Captured
        import r193_pipeline
        try:
            mapping=r193_pipeline.media_index(a.docx,a.project_media)
            r193_pipeline.generate(analysis_docx,mapping,"cut",a.model,a.device)
        except R220Captured as done:
            result=done.detail
            print("AIVE_RESULT_JSON "+json.dumps(result,ensure_ascii=True),flush=True)
            return 0
        raise ValueError("R220_CAPTURE_NOT_EMITTED; refuz inserarea din plan legacy")
    except Exception as e:
        (ROOT/"Temp"/"R220").mkdir(parents=True,exist_ok=True)
        with (ROOT/"Temp"/"R220"/"last_error.log").open("a",encoding="utf8") as f:
            f.write(traceback.format_exc()+"\n")
        print("AIVE_RESULT_JSON "+json.dumps({"ok":False,"message":str(e)},
              ensure_ascii=True),flush=True)
        return 1
if __name__=="__main__":
    raise SystemExit(main())
