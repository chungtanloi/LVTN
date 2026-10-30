import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
RAG = ROOT / 'CPA2_KhaoSat/w14_rag'
sys.path.insert(0, str(RAG))

from build_clean_corpus import build
from grounded_answer import lookup_response, tra_cuu
from retriever import Retriever, source_documents


class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lookup = Retriever()
    def test_http_lookup_delivers_clean_clause_and_clarification(self):
        import os
        from fastapi.testclient import TestClient
        from cpa2_api.main import app
        with patch.dict(os.environ, {'CPA2_SERVICE_KEY': 'source-test-only'}), TestClient(app) as client:
            headers = {'Authorization': 'Bearer source-test-only'}
            result = client.post('/v1/lookup', headers=headers, json={'question': 'QĐ3266 Điều 22 khoản 4 quy định gì?'})
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()['passages'][0]['passage_id'], 'qd3266:D22:K4')
            self.assertEqual(result.headers['Cache-Control'], 'no-store')
            result = client.post('/v1/lookup', headers=headers, json={'question': 'Môn này có tiên quyết không?'})
            self.assertEqual(result.status_code, 200)
            self.assertTrue(result.json()['clarification']['message'])
            self.assertFalse(result.json()['passages'])

    def test_clean_sources_reproduce_and_preserve_every_formal_mapping(self):
        docs, notes = build()
        stored = list(source_documents().values())
        self.assertEqual(docs, stored)
        old = [json.loads(line) for line in (RAG / 'corpus.jsonl').read_text(encoding='utf-8').splitlines()]
        by_id = {d['id']: d for d in docs}
        for doc in old:
            for field in ('rules', 'asp', 'van_ban', 'dieu', 'khoan'):
                self.assertEqual(doc.get(field), by_id[doc['id']].get(field))
        self.assertEqual(len(notes), 144)
        self.assertFalse(any('[PHÁT HIỆN ÂM TÍNH]' in d['text'] for d in docs))

    def test_ocr_merged_clause_is_split_and_addressable(self):
        docs = source_documents()
        self.assertNotIn('công bố', docs['qd3266:D22:K3']['text'])
        self.assertIn('công bố', docs['qd3266:D22:K4']['text'])
        result = tra_cuu('QĐ3266 Điều 22 khoản 4 quy định gì?', r=self.lookup)
        self.assertEqual([p['passage_id'] for p in result], ['qd3266:D22:K4'])
        self.assertEqual(result[0]['trang'], 14)
        self.assertEqual(tra_cuu('QĐ3266 Điều 22 khoản 40 quy định gì?', r=self.lookup), [])

    def test_free_text_publication_query_resolves_verified_split(self):
        result = tra_cuu('Điểm học phần sẽ được công bố và ghi nhận như thế nào?', r=self.lookup)
        self.assertEqual(result[0]['passage_id'], 'qd3266:D22:K4')

    def test_lookup_and_certificate_do_not_quote_analyst_notes(self):
        result = tra_cuu('QĐ3266 Điều 14 số tín chỉ đăng ký', r=self.lookup)
        for passage in result:
            self.assertNotIn('PHÁT HIỆN ÂM TÍNH', passage['text'])
            self.assertNotIn('KHÔNG có sàn', passage['text'])
        engine = Retriever(ranked=False)
        citations = engine.trich_dan({'grounding': {'passages': ['qd3266:D14:K0']}})
        self.assertNotIn('PHÁT HIỆN ÂM TÍNH', citations[0]['trich'])

    def test_ambiguous_course_and_personal_verdict_ask_for_context(self):
        for query in ('Môn này có tiên quyết không?', 'Em đủ điều kiện tốt nghiệp chưa?'):
            result = lookup_response(query, r=self.lookup)
            self.assertFalse(result['passages'])
            self.assertTrue(result['clarification']['message'])
        self.assertTrue(lookup_response('Điều kiện tốt nghiệp gồm những gì?', r=self.lookup)['passages'])
        self.assertTrue(lookup_response('Môn CT177 có tiên quyết là gì?', r=self.lookup)['passages'])

    def test_quantities_are_not_the_pronoun_toi_and_generic_grades_need_no_course(self):
        for query in ('Hết thời gian học tối đa mà chưa đủ điều kiện tốt nghiệp thì sao?',
                      'Môn này bị điểm F thì phải học lại không?',
                      'Bị đình chỉ thi thì môn đó bị 0 điểm hả?'):
            self.assertNotIn('clarification', lookup_response(query, r=self.lookup))


if __name__ == '__main__':
    unittest.main(verbosity=2)
