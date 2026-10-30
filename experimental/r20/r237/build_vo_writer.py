"""Build distinct safe R237 V5-only MOGRT writer from approved R20 executor.

Never mutate installed original r20_graphics.jsx. New writer validates exact
R220 montage mode, sequenceID and VO plan, while keeping original collision,
backup, per-element readback and rollback logic. No QE.
"""
from __future__ import annotations
import pathlib,hashlib
def replace_one(s,a,b):
    if s.count(a)!=1:raise ValueError("R237_APPROVED_JSX_ANCHOR_NOT_UNIQUE "+a[:90])
    return s.replace(a,b,1)
def derive(original):
    s=original.decode('utf-8')
    old="if(!p||p.schema!=='aive-r20-graphics-v1'||p.mode!=='independent'||!N.hasOwnProperty(p.module))"
    new="if(!p||p.schema!=='aive-r20-graphics-v1'||p.mode!=='montage_vo'||p.module!=='04'||p.r237Schema!=='aive-r237-vo-montage-v1'||p.timing!=='VO_RESERVE_ESTIMATED'||!N.hasOwnProperty(p.module))"
    s=replace_one(s,old,new)
    old="""    if(prev){var gap=a.startSeconds-prev.startSeconds-prev.durationSeconds;
        if(gap<-.01||gap>(prev.groupId===a.groupId?.13:p.separatorSeconds+.13))fail('Gap/overlap nepermis');}"""
    new="""    if(prev && a.startSeconds<prev.startSeconds+prev.durationSeconds-.01)
      fail('R237 VO MOGRT OVERLAP');"""
    s=replace_one(s,old,new)
    old="    return N[p.module];"
    new="""    if(!p.sequenceId||!/^[a-f0-9]{64}$/.test(text(p.montagePlanSHA256)))
       fail('R237 MONTAGE PLAN IDENTITY INVALID');
    if(!p.limits||p.limits.charactersPerLine!==28||p.limits.lines!==4)
       fail('R237 VERTICAL SAFE ZONE MISSING');
    for(var k=0;k<p.items.length;k++){
      var line=p.items[k].physicalLines;
      for(var n=0;n<4;n++)if(line[n].length>28)fail('R237 V5 >28 chars');
    }
    return N[p.module];"""
    s=replace_one(s,old,new)
    old="function loadContext(path){var d=load(path),s=sequence(d.index);return {data:d,seq:s,track:s.videoTracks[d.index]};}"
    new="""function loadContext(path){
    var d=load(path),s=sequence(d.index);
    if(String(s.sequenceID||s.id)!==String(d.plan.sequenceId)||
       String(s.name).indexOf('[AIVE TEST]')<0)
      fail('R237 SEQUENCE CHANGED OR NOT AIVE TEST COPY');
    return {data:d,seq:s,track:s.videoTracks[d.index]};
  }"""
    s=replace_one(s,old,new)
    s=s.replace("$._AIVE_R20_", "$._AIVE_R237_VO_")
    if s.count("$._AIVE_R237_VO_")!=1:raise ValueError("R237_NAME_REPLACEMENT_FAILED")
    if "app.enableQE" in s:raise ValueError("QE_FORBIDDEN")
    for required in ("otherPrint(", "rollback(", "clipPrint(", "MOGRT READBACK nereușit",
                     "t.initialCount", "policy!=='zero'", "textLine0"):
        if required not in s:raise ValueError("SAVED_GUARD_MISSING "+required)
    return s.encode('utf8')
if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("--source",required=True);a.add_argument("--output",required=True)
    opts=a.parse_args()
    original=pathlib.Path(opts.source).read_bytes()
    out=derive(original)
    p=pathlib.Path(opts.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(out)
    print("R237 JSX generated",hashlib.sha256(out).hexdigest(),len(out))
