"""The text residents read and how their replies are parsed. No model is called."""

import re
from types import SimpleNamespace

from rations.agents import FRAMES, IDLE, parse, rules, turn
from rations.game import LEVELS, NAMES, play


def reply(*calls):
    return SimpleNamespace(tool_calls=[{'name': 'act', 'args': args, 'id': str(i)} for i, args in enumerate(calls)])


def test_parse_accepts_a_valid_act_and_drops_empty_gifts():
    act, problem = parse(
        reply({'say': 'hi', 'claim': 2, 'give': [{'to': 'Ben', 'amount': 1}, {'to': 'Cal', 'amount': 0}]})
    )
    assert problem is None and act == {'say': 'hi', 'claim': 2, 'give': [('Ben', 1)]}


def test_parse_turns_invalid_output_into_doing_nothing():
    for bad in (
        reply(),
        reply({'say': '', 'claim': -1, 'give': []}),
        reply({'say': '', 'claim': 1.5, 'give': []}),
        reply({'say': '', 'claim': 1, 'give': [{'to': 'Zed', 'amount': 1}]}),
    ):
        act, problem = parse(bad)
        assert act == IDLE and problem


def test_no_text_tells_a_resident_what_to_want():
    days = []

    def decide(day, morning, so_far):
        days.append((morning, list(so_far)))
        return {n: {'say': '', 'claim': 1, 'give': []} for n in morning['alive']}

    play(3, 'short', decide)
    for frame in FRAMES:
        for level in LEVELS:
            texts = [rules(frame, level, 'Ada', NAMES)] + [turn(frame, level, 'Ada', m, d) for m, d in days]
            for text in texts:
                assert not re.search(r'\b(win|score|goal|should|try to|survive|want)\b', text, re.IGNORECASE)
