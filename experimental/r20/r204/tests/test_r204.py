"""Synthetic R2.0.4 semantic compact layout tests; private editorial content excluded."""
import sys,types,unittest
from pathlib import Path

# Narrow stand-in only for the proprietary legacy pagination function.
legacy=types.ModuleType("r171_layout")
legacy.clean=lambda x:" ".join(x.split())
def paginate(src):
    words=legacy.clean(src).split();pages=[];lines=[];line=[]
    for word in words:
        if len(word)>33:raise ValueError("oversize token")
        new=" ".join(line+[word])
        if len(new)>33:
            lines.append(" ".join(line));line=[word]
            if len(lines)==4:
                pages.append((" ".join(lines), [""]*0+lines));lines=[]
        else:line.append(word)
    if line:lines.append(" ".join(line))
    if lines:pages.append((" ".join(lines),lines))
    return pages
legacy.split_cards=paginate;sys.modules["r171_layout"]=legacy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"candidate/tools"))
from r204_carton_layout import build_pages,compact_lines,semantic_emphasis

class TestR204(unittest.TestCase):
    def test_compact_single_line(self):
        p=build_pages("Bugetul crește cu 35%.")[0]
        self.assertEqual(sum(bool(s) for s in p["physicalLines"]),1)
        self.assertEqual(p["physicalLines"][3],"Bugetul crește cu 35%.")
        self.assertTrue(p["boldWords"]["3"])
    def test_min_rows(self):
        p=build_pages("În acest an, 250 de elevi învață o profesie nouă la școală.")[0]
        self.assertEqual(sum(bool(s) for s in p["physicalLines"]),2)
    def test_unicode_original(self):
        s="Școala din Chișinău are 12,5% mai mulți elevi – în anul 2026."
        p=build_pages(s)
        self.assertEqual(" ".join(x["text"] for x in p),s)
        self.assertTrue(any(any(y["reason"]=="numeric" for y in x["emphasisPhrases"]) for x in p))
    def test_indices_are_valid(self):
        p=build_pages("În școală învață 250 de elevi, iar 65% aleg profesii noi.")[0]
        for i,s in enumerate(p["physicalLines"]):
            assert len(s)<=33
            for pos in p["boldWords"][str(i)].split():
                self.assertGreaterEqual(int(pos),1)
                self.assertLessEqual(int(pos),len(s.split()))
    def test_no_extra_rows(self):
        self.assertEqual(len(compact_lines("Școala pregătește elevi.",set())),4)
        self.assertEqual(sum(bool(x) for x in compact_lines("Școala pregătește elevi.",set())),1)
    def test_reject_oversize(self):
        with self.assertRaises(ValueError):compact_lines("X"*34,set())
    def test_deterministic(self):
        s="250 de elevi au primit 65% sprijin pentru formarea profesională."
        self.assertEqual(build_pages(s),build_pages(s))
    def test_multi_page_word_preservation(self):
        s=" ".join(["Proiectul oferă 30 de locuri pentru elevi și profesori."]*8)
        p=build_pages(s)
        self.assertGreater(len(p),1)
        self.assertEqual(" ".join(x["text"] for x in p),s)
    def test_no_unrelated_rewrite(self):
        s="Astăzi s-au deschis trei grupe noi!"
        p=build_pages(s)
        self.assertEqual(" ".join(x["text"] for x in p),s)

if __name__=="__main__":unittest.main()
