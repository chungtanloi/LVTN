import copy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
RAG = ROOT / 'CPA2_KhaoSat/w14_rag'
sys.path.insert(0, str(RAG))
from retriever import Retriever
from cross_encoder import CrossRetriever
from grounded_answer import lookup_response


class CrossEncoderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = Retriever()
        cls.config = json.loads((RAG / 'retrieval_release_v6.json').read_text(encoding='utf-8'))

    def test_exact_course_and_unknown_reference_do_not_need_neural_execution(self):
        class Unavailable:
            def score(self, *args, **kwargs):
                raise AssertionError('Deterministic lookup must not load the neural model.')
        engine = CrossRetriever(self.base, Unavailable(), self.config)
        self.assertEqual(engine.search('Môn CT177 có tiên quyết là gì?', 1)[0][0]['ma_hp'], 'CT177')
        self.assertEqual(engine.search('Theo QĐ53390, công nhận điểm thế nào?'), [])
        self.assertEqual(engine.search('zzzxqv_kgjh'), [])

    def test_stale_source_or_manifest_is_rejected(self):
        for field in ('assets_sha256', 'source_corpus_sha256', 'source_bindings_sha256'):
            config = copy.deepcopy(self.config)
            config[field] = 'incorrect'
            with self.assertRaises(ValueError):
                CrossRetriever(self.base, object(), config)

    def test_neural_lookup_returns_original_grade_source(self):
        engine = CrossRetriever(self.base, config=self.config)
        result = lookup_response('điểm W', r=engine)
        self.assertEqual(result['passages'][0]['passage_id'], 'qd3266:D22:K5')
        for passage in result['passages']:
            self.assertEqual(passage['trich'], passage['text'][passage['excerpt_start']:passage['excerpt_end']])
        self.assertNotIn('verdict', result)

    def test_missing_model_fails_explicitly_instead_of_silently_using_old_search(self):
        from fastapi.testclient import TestClient
        from cpa2_api.main import app
        with patch.dict(os.environ, {'CPA2_SERVICE_KEY': 'cross-test-only',
                                     'CPA2_CROSS_ENCODER_DIR': str(RAG / 'absent-test-model')}), TestClient(app) as client:
            response = client.post('/v1/lookup', json={'question': 'điểm W'},
                                   headers={'Authorization': 'Bearer cross-test-only'})
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('passages', response.json())
