"""Budget and response regressions, runnable with the stdlib test runner."""
import sys
import unittest
from unittest.mock import patch

import transcripto
import transcripto_jev as j


class InvalidResponseTests(unittest.TestCase):
    def test_invalid_budget_is_refused_before_transport(self):
        for budget in [float('nan'), float('inf'), -1, 0]:
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                j.JevDetector('unused', max_usd=budget)

    def test_invalid_probability_has_no_verdict(self):
        for probability in ['nan', 'inf', -1, 2, True]:
            with self.subTest(probability=probability):
                response = {'answers': {'kind': {'probabilities': {'correction': probability}}}}
                self.assertEqual(j.parse_answers(response, 1), [None])

    def test_valid_probability_remains_scoreable(self):
        for probability in [0, 1, 0.5]:
            with self.subTest(probability=probability):
                response = {'answers': {'kind': {'probabilities': {'correction': probability}}}}
                self.assertEqual(j.parse_answers(response, 1), [probability])

    def test_cli_refuses_invalid_budget(self):
        for budget in ['nan', 'inf', '-1', '0']:
            argv = ['transcripto', 'coach', '--detector', 'jev',
                    '--jev-max-usd', budget, '--jev-dry-run']
            with self.subTest(budget=budget), patch.object(sys, 'argv', argv):
                with self.assertRaises(SystemExit) as exc:
                    transcripto.main()
                self.assertEqual(exc.exception.code, 2)

    def test_unknown_cost_stops_subsequent_requests(self):
        for cost in [None, 'unknown', float('nan'), float('inf'), -1]:
            with self.subTest(cost=cost):
                calls = []
                detector = j.JevDetector('unused', notice=lambda _: None)

                def call(texts):
                    calls.append(texts)
                    return [0.7] * len(texts), cost, j.MODEL

                detector._call = call
                result = detector.score(['fix parser', 'change test', 'retry build'])
                self.assertEqual(len(calls), 1)
                self.assertEqual(result, [True, None, None])
                self.assertIs(detector.stats['cost_unknown'], True)
                self.assertIs(detector.stats['budget_stopped'], True)
                self.assertEqual(detector.stats['budget_unsent'], 2)
                self.assertEqual(detector.stats['sent'], 1)
                self.assertEqual(detector.stats['eligible'], 3)
