"""The saved denominator cannot move when live requests or results change."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import transcripto_coaching as coaching
import transcripto_continuity as continuity


class PinnedCoachingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'one.jsonl'
        self.baseline = self.root / 'baseline.json'

    def tearDown(self):
        self.temp.cleanup()

    def request(self, text):
        return {'type': 'user', 'sessionId': 'one', 'promptSource': 'typed', 'message': {'content': text}}

    def append(self, *rows):
        with self.source.open('a') as stream:
            stream.write(''.join(json.dumps(r) + '\n' for r in rows))

    def snapshot(self):
        return coaching.snapshot([str(self.source)], [str(self.root)])

    def test_new_requests_and_updated_prior_outcomes_have_separate_populations(self):
        self.append(self.request('PRIVATE REQUEST BODY'))
        baseline = self.snapshot()
        self.assertNotIn('PRIVATE REQUEST BODY', json.dumps(baseline))
        continuity.write_private(self.baseline, baseline)
        frozen = self.baseline.read_bytes()
        self.append({'type': 'assistant', 'message': {'content': 'No code change needed'}},
                    self.request('Make the next change'),
                    {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Edit', 'id': 'e', 'input': {'file_path': 'app.py'}}]}})
        comparison = coaching.compare(self.snapshot(), str(self.baseline))
        self.assertEqual(comparison['baseline']['summary']['requests'], 1)
        self.assertEqual(comparison['newly_observed']['summary']['requests'], 1)
        self.assertEqual(len(comparison['updated_prior_outcomes']), 1)
        self.assertEqual(comparison['newly_observed']['summary']['groups'][0]['unknown_change_requests'], 1)
        self.assertEqual(self.baseline.read_bytes(), frozen)
        self.assertEqual(comparison['baseline']['sha256'], hashlib.sha256(frozen).hexdigest())

    def test_rewritten_old_request_is_not_new_work(self):
        self.append(self.request('Keep option A'))
        continuity.write_private(self.baseline, self.snapshot())
        self.source.write_text(self.source.read_text().replace('option A', 'option B'))
        comparison = coaching.compare(self.snapshot(), str(self.baseline))
        self.assertEqual(comparison['newly_observed']['summary']['requests'], 0)
        self.assertEqual(len(comparison['changed_prior_requests']), 1)

    def test_correct_read_only_answer_has_no_failure_rate(self):
        self.append(self.request('Should anything change?'), {'type': 'assistant', 'message': {'content': 'No, the behavior already matches the requirement.'}})
        group = self.snapshot()['summary']['groups'][0]
        self.assertEqual(group['answers_without_observed_change'], 1)
        self.assertEqual(group['requests_with_failed_result'], 0)
        self.assertIsNone(group['successful_change_result_fraction'])
        self.assertIsNone(group['wilson_95_interval'])

    def test_empty_return_visit_does_not_invent_an_improvement(self):
        self.append(self.request('Keep the parser'))
        continuity.write_private(self.baseline, self.snapshot())
        comparison = coaching.compare(self.snapshot(), str(self.baseline))
        self.assertEqual(comparison['newly_observed']['summary'], {'requests': 0, 'groups': []})
        self.assertEqual(comparison['changed_prior_requests'], [])
        self.assertEqual(comparison['updated_prior_outcomes'], [])


if __name__ == '__main__':
    unittest.main()
