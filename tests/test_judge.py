"""Threshold calibration: a question is reported only if its threshold holds on held-out reference labels."""

import json

from rations import judge


def test_calibration_reports_a_separable_question_and_drops_a_noisy_one(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # results/ is relative
    (tmp_path / 'results' / 't').mkdir(parents=True)
    calls, cache, reference = [], [], []
    for i in range(80):
        text, positive = f'reasoning number {i}', i % 2 == 0
        calls.append({'resident': 'Ada', 'day': i, 'reply': [{'type': 'thinking', 'thinking': text}]})
        noise = 0.9 if i % 4 < 2 else 0.1  # unrelated to the label
        yes = {q: 0.1 for q in judge.QUESTIONS} | {'fairness': 0.9 if positive else 0.1, 'self_survival': noise}
        cache.append({'digest': judge.digest(text), 'key': f'x/Ada/{i}', 'yes': yes})
        labels = {q: 'no' for q in judge.QUESTIONS} | {
            'fairness': 'yes' if positive else 'no',
            'self_survival': 'yes' if i % 2 == 0 else 'no',
        }
        reference += [{'digest': judge.digest(text), 'pass': p, 'labels': labels} for p in (1, 2)]
    (tmp_path / 'results' / 't' / 'x.json').write_text(json.dumps({'calls': calls}))
    (tmp_path / 'results' / 'jev.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in cache))
    (tmp_path / 'results' / 'labels').mkdir()
    (tmp_path / 'results' / 'labels' / 'reference.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in reference))

    judge.calibrate('t', 0)

    result = json.loads((tmp_path / 'results' / 'thresholds.json').read_text())
    assert result['fairness']['reported'] and result['fairness']['held_out_precision'] == 1.0
    assert not result['self_survival']['reported']
    assert not result['test_awareness']['reported']  # never labelled yes, so no threshold can be set
