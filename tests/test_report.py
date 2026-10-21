"""The report rebuilds from recordings alone. Scripted games stand in for model games."""

import json

from rations import goods, label
from rations.agents import FRAMINGS
from rations.game import LEVELS, play
from rations.report import report


def test_report_builds_every_experiment_from_recordings(offline, tmp_path):
    (tmp_path / 'results' / 't' / 'rations').mkdir(parents=True)
    for seed in range(3):
        for level in LEVELS:
            for frame in FRAMINGS:
                claim = 3 if frame == 'survival' else 0

                def decide(day, morning, days, claim=claim):
                    return {n: {'say': '', 'claim': claim, 'give': []} for n in morning['alive']}

                recording = {
                    'experiment': 'rations',
                    'seed': seed,
                    'level': level,
                    'framing': frame,
                    'status': 'complete',
                    'usd': 0.0,
                    'calls': [],
                    'days': play(seed, level, decide),
                }
                path = tmp_path / 'results' / 't' / 'rations' / f'{level}-{frame}-{seed:03d}.json'
                path.write_text(json.dumps(recording))
    offline('choose', lambda messages: {'choice': 'A' if 'Community' in messages[0].content else 'B'})
    label.run('t', range(3), cap=1)
    offline('split', lambda messages: {'group': 15 if '0.75' in messages[0].content else 5})
    goods.run('t', range(3), cap=1)

    report('t')

    text = (tmp_path / 'results' / 't' / 'report.md').read_text()
    assert '3 complete seeds' in text and 'Story: survival - game: +' in text
    assert 'Name, residents: Community - Stock Market: +1.000' in text
    assert 'Return: 0.75 - 0.3: +0.500' in text and 'Wording: positive - negative: +0.000' in text
    assert (tmp_path / 'results' / 't' / 'grid.png').exists() and (tmp_path / 'results' / 't' / 'goods.png').exists()


def test_failed_games_are_counted_not_averaged(offline, tmp_path):
    (tmp_path / 'results' / 't' / 'rations').mkdir(parents=True)
    failed = {'seed': 0, 'level': 'short', 'framing': 'game', 'status': 'failed', 'usd': 0.0, 'calls': [], 'days': []}
    (tmp_path / 'results' / 't' / 'rations' / 'short-game-000.json').write_text(json.dumps(failed))
    report('t')
    text = (tmp_path / 'results' / 't' / 'report.md').read_text()
    assert '1 games, 1 failed' in text and '| short | game | 0 |' in text
