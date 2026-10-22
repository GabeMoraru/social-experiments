"""Public goods: both wordings describe the same payoffs, and a game runs offline with scripted members."""

import json
import random

from social_experiments import goods


def test_the_negative_wording_describes_the_same_points():
    rng = random.Random(0)
    for r in goods.RETURNS.values():
        for _ in range(500):
            group = {seat: rng.randint(0, goods.TOKENS) for seat in goods.SEATS}
            kept = {seat: goods.TOKENS - g for seat, g in group.items()}
            # as the negative wording tells it: a kept token pays 1 and costs every other member r, a token in the
            # group account pays its owner r, and everyone gets a fixed amount
            told = {
                seat: kept[seat]
                - r * (sum(kept.values()) - kept[seat])
                + r * group[seat]
                + (goods.SIZE - 1) * goods.TOKENS * r
                for seat in goods.SEATS
            }
            assert all(abs(told[seat] - points) < 1e-9 for seat, points in goods.points(group, r).items())


def test_the_wordings_share_the_choice():
    for level in goods.RETURNS:
        positive, negative = (goods.instructions(level, w) for w in goods.WORDINGS)
        assert positive.split('\n- ')[0] == negative.split('\n- ')[0]  # the same lead-in, the same tool


def test_a_game_records_ten_rounds_and_an_invalid_split_keeps_everything(offline, tmp_path):
    # members put in 10 tokens, except seat 4's first message each round, which asks for an impossible 30
    def policy(messages):
        return {'group': 30 if 'Round 1 ' in messages[-1].content else 10}

    offline('split', policy)
    goods.run('t', range(1), cap=1)
    games = [json.loads(p.read_text()) for p in (tmp_path / 'results' / 't' / 'goods').glob('*.json')]
    assert len(games) == 4
    for g in games:
        assert g['status'] == 'complete' and len(g['rounds']) == goods.ROUNDS
        assert g['rounds'][0] == dict.fromkeys(goods.SEATS, 0) and g['rounds'][1] == dict.fromkeys(goods.SEATS, 10)
        assert sum(c['problem'] is not None for c in g['calls']) == goods.SIZE
