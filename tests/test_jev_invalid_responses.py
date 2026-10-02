import sys
import pytest
import transcripto_jev as j
import transcripto


@pytest.mark.parametrize('budget', [float('nan'), float('inf'), -1, 0])
def test_invalid_budget_is_refused_before_transport(budget):
    with pytest.raises(ValueError):
        j.JevDetector('unused', max_usd=budget)


@pytest.mark.parametrize('probability', ['nan', 'inf', -1, 2, True])
def test_invalid_probability_has_no_verdict(probability):
    response = {'answers': {'kind': {'probabilities': {'correction': probability}}}}
    assert j.parse_answers(response, 1) == [None]


@pytest.mark.parametrize('probability', [0, 1, 0.5])
def test_valid_probability_remains_scoreable(probability):
    response = {'answers': {'kind': {'probabilities': {'correction': probability}}}}
    assert j.parse_answers(response, 1) == [probability]


@pytest.mark.parametrize('budget', ['nan', 'inf', '-1', '0'])
def test_cli_refuses_invalid_budget(monkeypatch, budget):
    monkeypatch.setattr(sys, 'argv', ['transcripto', 'coach', '--detector', 'jev',
                                    '--jev-max-usd', budget, '--jev-dry-run'])
    with pytest.raises(SystemExit) as exc:
        transcripto.main()
    assert exc.value.code == 2


@pytest.mark.parametrize('cost', [None, 'unknown', float('nan'), float('inf'), -1])
def test_unknown_cost_stops_subsequent_requests(cost):
    calls = []
    detector = j.JevDetector('unused', notice=lambda _: None)
    def call(texts):
        calls.append(texts)
        return [0.7] * len(texts), cost, j.MODEL
    detector._call = call
    result = detector.score(['fix parser', 'change test', 'retry build'])
    assert len(calls) == 1
    assert result == [True, None, None]
    assert detector.stats['cost_unknown'] is True
    assert detector.stats['budget_stopped'] is True
    assert detector.stats['budget_unsent'] == 2
    assert detector.stats['sent'] == 1
    assert detector.stats['eligible'] == 3
