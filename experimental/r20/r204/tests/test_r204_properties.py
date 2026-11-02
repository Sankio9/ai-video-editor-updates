"""R2.0.4 candidate property tests. Synthetic Romanian only, no user material.
Verify lossless wrapping, physical MOGRT rows, Bold indexes and repeatability.
Tests add coverage; they do not certify Adobe Premiere rendering.
"""
from __future__ import annotations
import random
import unittest
from test_r204 import build_pages

SYNTHETIC_WORDS = [
    "Școala", "Profesională", "Bubuieci", "programul", "oferă",
    "250", "de", "elevi", "proiectul", "are", "30%", "investiții",
    "pentru", "tineri", "și", "profesori", "în", "2026", "la",
    "Chișinău", "oportunități", "cursuri", "noi", "educație.",
    "învățământului", "modernizare,", "comunității", "euro"
]

class TestR204Properties(unittest.TestCase):
    def test_seeded_200_inputs_preserve_copy_and_bold_indices(self):
        r = random.Random(27102026)
        for case in range(200):
            original = " ".join(r.choice(SYNTHETIC_WORDS) for _ in range(r.randint(2, 85)))
            with self.subTest(case=case):
                pages = build_pages(original)
                self.assertTrue(pages)
                self.assertEqual(" ".join(p["text"] for p in pages), original)
                for p in pages:
                    self.assertEqual(len(p["physicalLines"]), 4)
                    self.assertEqual(" ".join(s for s in p["physicalLines"] if s), p["text"])
                    self.assertEqual(set(p["boldWords"]), {"0", "1", "2", "3"})
                    for row, line in enumerate(p["physicalLines"]):
                        self.assertLessEqual(len(line), 33)
                        for word in p["boldWords"][str(row)].split():
                            self.assertTrue(word.isdecimal())
                            self.assertTrue(1 <= int(word) <= len(line.split()))
    def test_unicode_numerics_no_fabrication(self):
        for src in [
            "În Chișinău, școala are 25% mai mulți elevi.",
            "Costul este 12,5 milioane de lei.",
            "Proiectul din anul 2026 oferă 100 de locuri.",
            "Șase grupe noi în cadrul școlii profesionale.",
            "Programul pentru ÎNVĂȚĂMÂNT și EDUCAȚIE.",
        ]:
            with self.subTest(src=src):
                pages = build_pages(src)
                self.assertEqual(" ".join(p["text"] for p in pages),src)
                self.assertTrue(all(len(s)<=33 for p in pages for s in p["physicalLines"]))
    def test_replay_is_deterministic(self):
        sample="Programul oferă 250 de locuri în școala profesională."
        self.assertEqual(build_pages(sample),build_pages(sample))

if __name__ == "__main__":
    unittest.main()
