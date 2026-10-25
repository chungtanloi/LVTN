"""Runtime ranking invariants, frozen source provenance and dev acceptance gates.

Never selects model parameters or evaluates the fresh holdout during regression.
"""
import hashlib
import json
from pathlib import Path
import unittest

from retriever import Retriever

HERE = Path(__file__).parent


class RankingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ranked = Retriever(ranked=True)
        cls.legacy = Retriever(ranked=False)

    def test_exact_curriculum_entity_is_preserved(self):
        result = self.ranked.search('Môn CT177 có tiên quyết là gì?', k=1)
        self.assertEqual(result[0][0]['ma_hp'], 'CT177')

    def test_explicit_regulation_and_filters(self):
        result = self.ranked.search('Theo QĐ5339, công nhận điểm ở trường khác như thế nào?', k=5)
        self.assertTrue(result)
        self.assertTrue(all(d['van_ban'] == 'qd5339' for d, _ in result))
        self.assertEqual(self.ranked.search('Điểm W', van_ban='not-in-corpus'), [])
        self.assertTrue(all(d['loai'] == 'ctdt' for d, _ in self.ranked.search('tiên quyết', loai='ctdt')))

    def test_returns_only_original_source_text(self):
        for doc, score in self.ranked.search('số tín chỉ học lại vượt bao nhiêu thì bị hạ bằng?', 5):
            self.assertEqual(doc['text'], self.ranked.by_id[doc['id']]['text'])
            self.assertNotIn('synthetic_survey_train', doc['text'])
            self.assertIsInstance(score, float)

    def test_grounding_does_not_depend_on_ranking(self):
        for rule in self.legacy.by_asp:
            self.assertEqual(self.ranked.ground_rule(rule), self.legacy.ground_rule(rule))

    def test_examples_are_train_only_and_disjoint_from_holdout(self):
        training = json.loads((HERE / 'rag_survey_train_sources_v1.json').read_text(encoding='utf-8'))['queries']
        holdout = json.loads((HERE / 'rag_survey_holdout_v1.json').read_text(encoding='utf-8'))['queries']
        self.assertTrue(all(q['split'] == 'train' for q in training))
        self.assertFalse({q['id'] for q in training} & {q['id'] for q in holdout})
        self.assertFalse({q['group'] for q in training} & {q['group'] for q in holdout})
        for q in training:
            self.assertTrue(set(q['gold']) <= set(self.ranked.by_id))

    def test_dev_targets_and_no_holdout_configuration(self):
        config = json.loads((HERE / 'retrieval_model_v1.json').read_text(encoding='utf-8'))
        self.assertEqual(config['selection_split'], 'dev')
        self.assertFalse(config['holdout_used_for_selection'])
        queries = [q for q in json.loads((HERE / 'rag_queries.json').read_text(encoding='utf-8'))['queries'] if q['split'] == 'dev']
        hits = []
        for q in queries:
            ids = [d['id'] for d, _ in self.ranked.search(q['q'], 5)]
            hits.append((ids[0] in q['gold'], bool(set(ids) & set(q['gold']))))
        self.assertGreaterEqual(sum(h[0] for h in hits) / len(hits), .80)
        self.assertGreaterEqual(sum(h[1] for h in hits) / len(hits), .95)


if __name__ == '__main__':
    unittest.main(verbosity=2)
