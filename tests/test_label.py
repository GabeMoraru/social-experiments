"""The Name of the Game: the arms differ only in the name, and the computer copies the recorded resident arm."""

import json

from social_experiments import label


def test_the_arms_differ_only_in_the_name():
    for opponent in label.OPPONENTS:
        community = label.instructions('community', opponent).replace('Community Game', 'X')
        assert community == label.instructions('stock_market', opponent).replace('Stock Market Game', 'X')


def test_the_text_states_the_payoffs():
    text = label.instructions('community', 'resident')
    for (mine, theirs), (you, them) in label.POINTS.items():
        assert f'you choose {mine} and the other participant chooses {theirs}, you get {you} points' in text


def test_the_computer_chooses_a_as_often_as_the_resident_arm_did(offline, tmp_path):
    # residents in the Community Game choose A, in the Stock Market Game B
    def policy(messages):
        return {'choice': 'A' if 'Community' in messages[0].content else 'B'}

    offline('choose', policy)
    label.run('t', range(3), cap=1)
    games = [json.loads(p.read_text()) for p in sorted((tmp_path / 'results' / 't' / 'label').glob('*.json'))]
    assert len(games) == 12 and all(g['status'] == 'complete' for g in games)
    for g in games:
        if g['opponent'] == 'computer':
            rate = 1.0 if g['label'] == 'community' else 0.0
            assert g['computer_rate'] == rate and set(g['computer'].values()) == {'A' if rate else 'B'}
    assert label.share_a([g for g in games if g['label'] == 'community']) == 1.0


def test_an_invalid_choice_counts_as_neither():
    assert label.share_a([{'choices': {'1': 'A', '2': None}}]) == 1.0
    assert label.share_a([{'choices': {'1': None, '2': None}}]) is None
