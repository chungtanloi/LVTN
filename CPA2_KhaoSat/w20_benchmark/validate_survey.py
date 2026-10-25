"""Synthetic survey ingestion/training regression checks; no holdout evaluation."""
import csv
import json
from pathlib import Path
import tempfile
import unittest

from survey_training import prepare, train


class SurveyTests(unittest.TestCase):
    def test_generated_artifacts_keep_groups_and_questions_disjoint(self):
        directory = Path(__file__).parent / 'qreal/synthetic_survey'
        ids, groups, questions = {}, {}, {}
        for split in ('train', 'dev', 'test'):
            rows = [json.loads(line) for line in (directory / (split + '.jsonl')).read_text(encoding='utf-8').splitlines()]
            for row in rows:
                self.assertEqual(row['split'], split)
                self.assertEqual(row['source'], 'synthetic_survey')
                for mapping, key in ((ids, row['id']), (groups, row['group']), (questions, row['question'].casefold())):
                    self.assertIn(mapping.get(key, split), (split,))
                    mapping[key] = split
        manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['real_question_count'], 0)
        self.assertEqual(len(ids), manifest['unique_questions'])

    def write(self, rows, path):
        fields = ['id', 'dong_y', 'nguon', 'cau_hoi_1', 'cau_hoi_1_intent', 'cau_hoi_1_kieu']
        with path.open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_consent_anonymization_duplicate_groups_and_stability(self):
        rows = [{'id': str(i), 'dong_y': 'Tôi đồng ý', 'nguon': 'SYNTHETIC',
                 'cau_hoi_1': q, 'cau_hoi_1_intent': 'dang_ky', 'cau_hoi_1_kieu': 'chuan'}
                for i, q in enumerate(['Em B2306555 xin đăng ký môn', 'Em B2306555 xin đăng ký môn', 'Tôi x@example.com xin đăng ký môn'])]
        rows.append({**rows[0], 'id': 'no', 'dong_y': 'Không đồng ý', 'cau_hoi_1': 'excluded question'})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'survey.csv'
            self.write(rows, path)
            output, meta = prepare(path)
            self.assertEqual(meta['raw_questions'], 3)
            self.assertEqual(len(output), 2)
            self.assertEqual(meta['real_question_count'], 0)
            self.assertNotIn('B2306555', str(output))
            self.assertNotIn('x@example.com', str(output))
            self.write(list(reversed(rows)), path)
            again, _ = prepare(path)
            self.assertEqual({r['id']: (r['split'], r['group']) for r in output},
                             {r['id']: (r['split'], r['group']) for r in again})

    def test_real_source_rejected_in_synthetic_pipeline(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'survey.csv'
            self.write([{'id': 'x', 'dong_y': 'Tôi đồng ý', 'nguon': 'real'}], path)
            with self.assertRaises(ValueError):
                prepare(path)

    def test_holdout_does_not_enter_training_or_tuning(self):
        records = [{'id': 'train', 'split': 'train', 'intent': 'a', 'question': 'registration'},
                   {'id': 'dev', 'split': 'dev', 'intent': 'a', 'question': 'registration'},
                   {'id': 'test', 'split': 'test', 'intent': 'secret', 'question': 'private_holdout'}]
        model = train(records)
        self.assertNotIn('private_holdout', model['vocabulary'])
        self.assertNotIn('secret', model['documents'])
        self.assertEqual(model['meta']['training_ids'], ['train'])
        self.assertEqual(model['meta']['tuning_ids'], ['dev'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
