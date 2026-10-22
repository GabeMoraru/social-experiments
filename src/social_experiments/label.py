"""The Name of the Game: a one-shot choice between A and B whose arms differ only in the game's name.

Copied from study 1 of Ellingsen, Johannesson, Mollerstrom & Munkhammar (2012). In people, calling it the Community
Game rather than the Stock Market Game raises the share choosing A when another person chooses too, and not when a
computer does, so the name works through what people expect of each other. Each decision is one fresh call.
"""

import random
from concurrent.futures import ThreadPoolExecutor

from social_experiments import agents
from social_experiments.run import charge, check, game_path, load, record

LABELS = {'community': 'Community Game', 'stock_market': 'Stock Market Game'}
OPPONENTS = ('resident', 'computer')  # the resident arm is played first: the computer copies its choices
SEATS = ('1', '2')  # two decisions a game: a pair, or two residents each facing its own computer
# (your choice, the other side's choice): (your points, the other's points)
POINTS = {('A', 'A'): (50, 50), ('B', 'B'): (20, 20), ('A', 'B'): (5, 80), ('B', 'A'): (80, 5)}

OTHER = {
    'resident': """In the {game} you are paired with another participant. You will not learn who they are, and \
they will not learn who you are. You both get the same instructions.""",
    'computer': """In the {game} you are paired with a computer. A receiver is connected to the computer: another \
participant, who makes no choice and gets the points the computer is allotted. The receiver does not learn which \
game was played, or how you or the computer chose.

The computer chooses like this: the {game} is also played between two participants, and the computer chooses A as \
often as they did, to imitate a participant.""",
}
SIDES = {'resident': ('the other participant', 'the other participant'), 'computer': ('the computer', 'the receiver')}
TEXT = """You are taking part in the {game}. You get points, and how many depends on the choices made.

{other}

You and {chooser} choose at the same time between A and B. In the {game}:
{points}

You will not know anything about the choice of {chooser} when you make yours. Give your choice with the choose \
tool."""

TOOL = {
    'name': 'choose',
    'description': 'Your choice.',
    'strict': True,
    'input_schema': {
        'type': 'object',
        'additionalProperties': False,
        'required': ['choice'],
        'properties': {'choice': {'type': 'string', 'enum': ['A', 'B']}},
    },
}


def instructions(label, opponent):
    game, (chooser, getter) = LABELS[label], SIDES[opponent]
    points = '\n'.join(
        f'- If you choose {mine} and {chooser} chooses {theirs}, you get {you} points and {getter} gets {them}.'
        for (mine, theirs), (you, them) in POINTS.items()
    )
    return TEXT.format(game=game, other=OTHER[opponent].format(game=game), chooser=chooser, points=points)


def parse(reply):
    return agents.one_call(reply, 'choose', 'choice', lambda value: value in ('A', 'B'))


def share_a(games):
    """The share choosing A among valid choices; an invalid choice is neither A nor B and is counted apart."""
    valid = [c for g in games for c in g['choices'].values() if c]
    return sum(c == 'A' for c in valid) / len(valid) if valid else None


def play_game(seed, label, opponent, rate, cap, model):
    """Two decisions, made at once. Against the computer, each faces its own draw at the given rate of A."""
    text, name, calls = instructions(label, opponent), f'label-{label}-{opponent}-{seed:03d}', []

    def one(seat):
        choice, record = agents.Resident(model, text, TOOL).act('Choose A or B.', parse)
        charge(name, record['usd'])
        calls.append({'resident': seat, 'day': 1} | record)
        return choice

    try:
        check(cap)
        with ThreadPoolExecutor(len(SEATS)) as pool:
            choices, status, error = dict(zip(SEATS, pool.map(one, SEATS))), 'complete', None
    except BaseException as e:  # noqa: BLE001 - any failure, an interrupt included, is recorded, never retried
        choices, status, error = {}, 'failed', f'{type(e).__name__}: {e}'
    computer = None
    if opponent == 'computer':
        computer = {seat: 'A' if random.Random(f'computer {seed} {seat}').random() < rate else 'B' for seat in SEATS}
    return {
        'experiment': 'label',
        'seed': seed,
        'label': label,
        'opponent': opponent,
        'model': agents.MODEL,
        'settings': agents.SETTINGS,
        'text': text,
        'computer_rate': rate,
        'computer': computer,
        'status': status,
        'error': error,
        'usd': sum(c['usd'] for c in calls),
        'choices': choices,
        'calls': sorted(calls, key=lambda c: c['resident']),
    }


def run(tag, seeds, cap):
    """The resident arm for every seed, then the computer arm, whose rate of A is the resident arm's for that name."""
    model = agents.chat()
    for opponent in OPPONENTS:
        rates = {label: None for label in LABELS}
        if opponent == 'computer':
            for label in LABELS:
                pairs = [g for g in load(tag, 'label') if (g['label'], g['opponent']) == (label, 'resident')]
                rates[label] = share_a([g for g in pairs if g['status'] == 'complete'])
                if rates[label] is None:
                    raise SystemExit(f'No resident-arm choices for {label} in {tag}, so the computer has none to copy.')
        for seed in seeds:
            for label in LABELS:
                path = game_path(tag, 'label', (label, opponent), seed)
                if record(path, cap, play_game, seed, label, opponent, rates[label], cap, model):
                    return
