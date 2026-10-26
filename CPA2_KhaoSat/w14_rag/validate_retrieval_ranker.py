"""Runtime ranking invariants, frozen source provenance and dev acceptance gates.

Never selects model parameters or evaluates the fresh holdout during regression.
"""
import hashlib
import json
from pathlib import Path
import unittest
import tempfile

from retriever import Retriever, kiem_trich_dan
import grounded_answer

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

    def test_decision_numbers_are_not_prefix_matches(self):
        for number in ('326', '53390', '5339abc'):
            self.assertEqual(self.ranked.search(f'Theo QĐ{number}, công nhận điểm thế nào?', 3), [])
        result = self.ranked.search('Theo quyết định 5339, công nhận học phần thế nào?', 3)
        self.assertTrue(result)
        self.assertTrue(all(d['van_ban'] == 'qd5339' for d, _ in result))

    def test_no_lexical_evidence_returns_no_sources(self):
        for engine in (self.ranked, self.legacy):
            for question in ('zzzxqv_kgjh', ' \t'):
                self.assertEqual(engine.search(question, 3), [])

    def test_missing_source_blocks_the_actual_answer_pipeline(self):
        profile = json.loads((HERE.parent / 'w7_student_facts/students/sv_lvtn.json').read_text(encoding='utf-8'))
        profile['tc_cong_nhan'] = 0
        grounder = Retriever(ranked=False)
        grounder.by_asp.pop('r_a02')
        with tempfile.TemporaryDirectory(prefix='cpa2-source-test-') as directory:
            path = Path(directory) / 'synthetic.json'
            path.write_text(json.dumps(profile), encoding='utf-8')
            answer = grounded_answer.tra_loi('Em đủ điều kiện tốt nghiệp chưa?', str(path), r=grounder)
        self.assertEqual(answer['verdict'], 'BLOCKED')

    def test_certificate_does_not_silently_drop_the_claim_trace(self):
        profile = json.loads((HERE.parent / 'w7_student_facts/students/sv_lvtn.json').read_text(encoding='utf-8'))
        profile['tc_cong_nhan'] = 0
        with tempfile.TemporaryDirectory(prefix='cpa2-complete-proof-test-') as directory:
            path = Path(directory) / 'synthetic.json'
            path.write_text(json.dumps(profile), encoding='utf-8')
            answer = grounded_answer.tra_loi('Em đủ điều kiện tốt nghiệp chưa?', str(path))
        self.assertEqual(answer['verdict'], 'TRUE')
        steps = answer['certificate']['proof']['steps']
        self.assertTrue(any(step['atom'] == answer['claim'] for step in steps))
        self.assertGreater(len(steps), 20)
        self.assertEqual(steps[0]['atom'], answer['claim'])
        # 100 normal messages below 96 KiB each leave headroom within Convex's
        # 16 MiB read/return limits; every fact and source address is retained.
        self.assertLess(len(json.dumps(answer, ensure_ascii=False).encode('utf-8')), 96 * 1024)

    def certificate(self):
        return {'claim': 'tot_nghiep', 'verdict': 'TRUE', 'proof': {'steps': [
            {'atom': 'dat_nhom(g_chuyen_nganh)', 'rule_id': 'r_a02',
             'source': {'van_ban': 'qd3266', 'dieu': 7, 'khoan': 3}}]}}

    def test_why_annotation_is_not_itself_a_derived_fact(self):
        representative = {'dk_tin_chi', 'why(dk_tin_chi,r_f01a)', 'why(tot_nghiep,r_f01a)'}
        certificate = grounded_answer.prototype.build_certificate('tot_nghiep', 'FALSE',
            [representative], representative, representative)
        self.assertFalse(any(step['atom'] == 'tot_nghiep' for step in certificate['proof']['steps']))
        self.assertTrue(any(step['atom'] == 'dk_tin_chi' for step in certificate['proof']['steps']))

    def test_wrong_source_mapping_is_not_accepted(self):
        grounder = Retriever(ranked=False)
        grounder.by_asp['r_a02'] = grounder.by_asp['r_b03']
        certificate = grounder.ground_certificate(self.certificate())
        accepted, _ = kiem_trich_dan(certificate, [p['passage_id'] for p in grounder.trich_dan(certificate)])
        self.assertFalse(accepted)

    def test_regrounding_clears_stale_source_fields(self):
        certificate = self.legacy.ground_certificate(self.certificate())
        self.assertIn('passage_id', certificate['proof']['steps'][0])
        certificate['proof']['steps'][0]['rule_id'] = 'r_audit_missing'
        certificate = self.legacy.ground_certificate(certificate)
        self.assertNotIn('passage_id', certificate['proof']['steps'][0])
        self.assertFalse(kiem_trich_dan(certificate, [])[0])

    def test_source_must_exist_in_the_corpus_index(self):
        grounder = Retriever(ranked=False)
        passage = grounder.by_asp['r_a02']
        grounder.by_id.pop(passage['id'])
        certificate = grounder.ground_certificate(self.certificate())
        self.assertFalse(kiem_trich_dan(certificate, [])[0])

    def test_unknown_without_a_proof_does_not_require_a_citation(self):
        certificate = {'verdict': 'UNKNOWN', 'proof': {'steps': []}}
        certificate = self.legacy.ground_certificate(certificate)
        self.assertTrue(kiem_trich_dan(certificate, [])[0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
