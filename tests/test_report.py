"""The report rebuilds from recordings alone. Scripted games stand in for model games."""

import json

from rations.agents import FRAMINGS
from rations.game import LEVELS, play
from rations.report import report


def test_report_builds_from_recordings(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # results/ is relative, so the report reads and writes only here
    (tmp_path / 'results' / 't').mkdir(parents=True)
    for seed in range(3):
        for level in LEVELS:
            for frame in FRAMINGS:
                claim = 3 if frame == 'survival' else 0

                def decide(day, morning, days, claim=claim):
                    return {n: {'say': '', 'claim': claim, 'give': []} for n in morning['alive']}

                recording = {
                    'seed': seed,
                    'level': level,
                    'framing': frame,
                    'status': 'complete',
                    'usd': 0.0,
                    'calls': [],
                    'days': play(seed, level, decide),
                }
                (tmp_path / 'results' / 't' / f'{level}-{frame}-{seed:03d}.json').write_text(json.dumps(recording))
    report('t')
    text = (tmp_path / 'results' / 't' / 'report.md').read_text()
    assert '3 complete seeds' in text and 'Story: survival - game: +' in text
    assert (tmp_path / 'results' / 't' / 'grid.png').exists()


def test_failed_games_are_counted_not_averaged(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'results' / 't').mkdir(parents=True)
    failed = {'seed': 0, 'level': 'short', 'framing': 'game', 'status': 'failed', 'usd': 0.0, 'calls': [], 'days': []}
    (tmp_path / 'results' / 't' / 'short-game-000.json').write_text(json.dumps(failed))
    report('t')
    text = (tmp_path / 'results' / 't' / 'report.md').read_text()
    assert '1 games, 1 failed' in text and '| short | game | 0 |' in text
