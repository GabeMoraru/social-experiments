"""Judge calibration: a question is reported for a judge only if the judge holds up on held-out reference labels."""

import json

from rations import agents, judge


def test_calibration_reports_a_separable_question_and_drops_a_noisy_one(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # results/ is relative
    (tmp_path / 'results' / 't' / 'rations').mkdir(parents=True)
    calls, cache, verdicts, reference = [], [], [], []
    for i in range(80):
        text, positive = f'reasoning number {i}', i % 2 == 0
        calls.append({'resident': 'Ada', 'day': i, 'reply': [{'type': 'thinking', 'thinking': text}]})
        noise = 0.9 if i % 4 < 2 else 0.1  # unrelated to the label
        yes = {q: 0.1 for q in judge.QUESTIONS} | {'fairness': 0.9 if positive else 0.1, 'self_survival': noise}
        cache.append({'digest': judge.digest(text), 'key': f'rations/x/Ada/{i}', 'yes': yes})
        luna = {q: False for q in judge.QUESTIONS} | {'fairness': positive, 'self_survival': i % 3 == 0}
        verdicts.append({'digest': judge.digest(text), 'key': f'rations/x/Ada/{i}', 'yes': luna})
        labels = {q: 'no' for q in judge.QUESTIONS} | {
            'fairness': 'yes' if positive else 'no',
            'self_survival': 'yes' if i % 2 == 0 else 'no',
        }
        reference += [{'digest': judge.digest(text), 'pass': p, 'labels': labels} for p in (1, 2)]
    (tmp_path / 'results' / 't' / 'rations' / 'x.json').write_text(json.dumps({'calls': calls}))
    (tmp_path / 'results' / 'jev.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in cache))
    (tmp_path / 'results' / 'luna.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in verdicts))
    (tmp_path / 'results' / 'labels').mkdir()
    (tmp_path / 'results' / 'labels' / 'reference.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in reference))

    judge.calibrate('t', 0)

    result = json.loads((tmp_path / 'results' / 'thresholds.json').read_text())
    assert result['fairness']['reported'] and result['fairness']['held_out_precision'] == 1.0
    assert not result['self_survival']['reported']
    assert not result['test_awareness']['reported']  # never labelled yes, so no threshold can be set
    assert result['fairness']['luna_reported'] and result['fairness']['luna_kappa'] == 1.0
    assert result['fairness']['luna_jev_kappa'] == 1.0
    assert not result['self_survival']['luna_reported']


def test_kappa():
    assert judge.kappa([(True, True), (False, False)]) == 1.0
    assert judge.kappa([(True, False), (False, True)]) == -1.0


def test_the_judge_never_shares_a_provider_with_the_players():
    assert judge.LUNA.split('-')[0] != agents.MODEL.split('-')[0]


def test_label_all_asks_once_per_summary_and_resumes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'results' / 't' / 'rations').mkdir(parents=True)
    calls = [
        {'resident': 'Ada', 'day': i, 'reply': [{'type': 'thinking', 'thinking': f'text {i % 30}'}]} for i in range(60)
    ]
    (tmp_path / 'results' / 't' / 'rations' / 'x.json').write_text(json.dumps({'calls': calls}))
    asked = []
    monkeypatch.setitem(judge.JUDGES, 'fake', (judge.LUNA_CACHE, lambda text: asked.append(text) or {'fairness': True}))
    judge.label_all('t', 1, 'fake')
    judge.label_all('t', 1, 'fake')  # everything is cached, so nothing is asked again
    assert sorted(asked) == sorted({f'text {i}' for i in range(30)})
    assert len(judge.answers(judge.LUNA_CACHE)) == 30
