"""R2.0.5 local test candidate: generic colon concept prioritization, not based on real DOCX."""
from __future__ import annotations
import importlib.util
import pathlib
import random
import sys
import types
import unittest

HERE=pathlib.Path(__file__).resolve().parents[1]
ROOT=HERE.parents[0]
legacy=types.ModuleType('r171_layout')
legacy.clean=lambda s:' '.join(s.split())
def split_cards(s):
    words=legacy.clean(s).split()
    result=[];page=[];row=[]
    for word in words:
        proposed=' '.join(row+[word])
        if len(proposed)>33 and row:
            page.append(' '.join(row));row=[word]
        else:row.append(word)
        if len(page)>=4:
            result.append((' '.join(page),page))
            page=[]
    if row:page.append(' '.join(row))
    if page:result.append((' '.join(page),page))
    return result
legacy.split_cards=split_cards
sys.modules['r171_layout']=legacy

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

prev=load('layout204',HERE.parent/'r204'/'candidate'/'tools'/'r204_carton_layout.py')
new=load('layout205',HERE/'candidate'/'tools'/'r204_carton_layout.py')

class TestR205Semantics(unittest.TestCase):
    SAMPLE='UNII ELEVI ÎNVAȚĂ ÎN SISTEM DUAL: ȘI LA ȘCOALĂ, ȘI LA MUNCĂ'
    def test_colon_concept_wins(self):
        selected,spans=new.semantic_emphasis(self.SAMPLE)
        self.assertTrue(spans)
        self.assertEqual(spans[0]['text'],'SISTEM DUAL:')
        self.assertEqual(spans[0]['reason'],'concept_before_colon')
        self.assertTrue(set((4,5)).issubset(selected))
        self.assertFalse(set((1,2)).issubset(selected))
    def test_physical_bold_word_maps_cross_line(self):
        p=new.build_pages(self.SAMPLE)
        self.assertEqual(len(p),1)
        self.assertEqual(len([r for r in p[0]['physicalLines'] if r]),2)
        self.assertEqual(p[0]['text'],self.SAMPLE)
        marked=[]
        for i,row in enumerate(p[0]['physicalLines']):
            bold=set(int(x) for x in p[0]['boldWords'][str(i)].split())
            marked.extend(word for index,word in enumerate(row.split(),1) if index in bold)
        self.assertIn('SISTEM',marked)
        self.assertIn('DUAL:',marked)
        self.assertTrue(all(len(row)<=33 for row in p[0]['physicalLines']))
    def test_no_colon_same_as_r204(self):
        s='În această școală, 250 de elevi învață profesii pentru viitor.'
        self.assertEqual(new.build_pages(s),prev.build_pages(s))
    def test_skip_numeric_colon(self):
        s='Bugetul ajunge la 35%: elevii primesc sprijin.'
        _,spans=new.semantic_emphasis(s)
        self.assertFalse(any(x['reason']=='concept_before_colon' for x in spans))
    def test_unicode_and_no_editorial_rewrite(self):
        for s in ('Școala oferă meserii noi: elevii învață meseria.',
                  'Programul din Chișinău are 65% participare.',
                  'Învățământul dual: între școală și muncă.'):
            pages=new.build_pages(s)
            self.assertEqual(' '.join(p['text'] for p in pages),s)
            for p in pages:
                for i,line in enumerate(p['physicalLines']):
                    self.assertLessEqual(len(line),33)
                    self.assertTrue(all(1<=int(j)<=len(line.split()) for j in p['boldWords'][str(i)].split()))
    def test_seeded_200_short_inputs(self):
        rng=random.Random(270926)
        words='Școala oferă programe noi pentru elevi în anul 2026 și profesorii predau meserii.' .split()
        for _ in range(200):
            s=' '.join(rng.choice(words) for __ in range(rng.randint(3,12)))
            pages=new.build_pages(s)
            self.assertEqual(' '.join(p['text'] for p in pages),s)
            self.assertTrue(all(len(row)<=33 for p in pages for row in p['physicalLines']))

if __name__=='__main__':
    unittest.main(verbosity=2)
