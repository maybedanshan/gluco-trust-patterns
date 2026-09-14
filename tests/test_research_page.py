import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class PayloadParser(HTMLParser):
    def __init__(self):
        super().__init__();self.active=False;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag=='script' and dict(attrs).get('id')=='research-data':self.active=True
    def handle_endtag(self,tag):
        if tag=='script':self.active=False
    def handle_data(self,data):
        if self.active:self.parts.append(data)

class ResearchPageTests(unittest.TestCase):
    def test_embedded_label_summaries_exclude_meal_records(self):
        page=ROOT/'docs/demo/research.html'
        if not page.exists():self.skipTest('Build research page first')
        parser=PayloadParser();parser.feed(page.read_text(encoding='utf-8'))
        payload=json.loads(''.join(parser.parts))
        if 'labels' not in payload:self.skipTest('Label extension not bundled')
        self.assertEqual(len(payload['labels']),108)
        for summary in payload['labels']:
            self.assertNotIn('per_person',summary)
            self.assertNotIn('timestamp',summary)
            self.assertNotIn('target',summary)
            if summary['status']=='incomplete':
                self.assertGreater(summary['infeasible_people'],0)
                self.assertGreater(summary['infeasible_runs'],0)
            else:self.assertEqual(set(summary['ci95']),{'benefit','cost','joint_minus_input','joint_minus_label'})

if __name__=='__main__':unittest.main()
