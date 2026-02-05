import unittest
from src.doc_parser import parse_google_doc_text
from src.utils import normalize_date

SAMPLE_TEXT = """
2 Februari 2026

0730 - 1300 :
Meeting dan
Penyetaraan Desain
https://link.com/proof1

1400 - 1700 :
Coding
Bug Fix untuk Module X
https://github.com/repo/pr/123

3 Februari 2026

0900 - 1200 :
Research
Teknologi Baru
https://notion.so/research-notes
"""

class TestDocParser(unittest.TestCase):
    def test_parsing(self):
        entries = parse_google_doc_text(SAMPLE_TEXT)
        self.assertEqual(len(entries), 3)
        
        # Check first entry
        self.assertEqual(entries[0]['date_raw'], "2 Februari 2026")
        self.assertEqual(entries[0]['start_time'], "0730")
        self.assertEqual(entries[0]['end_time'], "1300")
        self.assertEqual(entries[0]['category'], "Meeting dan")
        self.assertEqual(entries[0]['description'], "Penyetaraan Desain")
        self.assertEqual(entries[0]['proof_link'], "https://link.com/proof1")

    def test_date_normalization(self):
        self.assertEqual(normalize_date("2 Februari 2026"), "2026-02-02")
        self.assertEqual(normalize_date("2026-02-02"), "2026-02-02")
        self.assertEqual(normalize_date("31 Januari 2026"), "2026-01-31")

if __name__ == '__main__':
    unittest.main()
