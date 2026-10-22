"""Public goods: four residents split tokens between their own account and a group account, for ten rounds.

Copied from the no-punishment partner arm of Fehr & Gächter (2000), with the two returns per token of Isaac & Walker
(1988) and the positive and negative wording of Andreoni (1995), closely paraphrased. The negative wording describes
the same payoffs as harm done by keeping tokens; the choice and the points are identical in both.
"""

from concurrent.futures import ThreadPoolExecutor

from social_experiments import agents
from social_experiments.run import charge, check, game_path, record

SIZE, ROUNDS, TOKENS = 4, 10, 20
RETURNS = {'low': 0.3, 'high': 0.75}  # points to every member per token in the group account
WORDINGS = ('positive', 'negative')
SEATS = tuple(str(n) for n in range(1, SIZE + 1))

ACCOUNTS = {
    'positive': """- Each token in your own account pays you 1 point.
- Each token in the group account pays {r:g} points to every member of the group, you included, whoever put it \
there.""",
    'negative': """- Each token in your own account pays you 1 point and lowers the points of every other member by \
{r:g}. In the same way, every token another member keeps in their own account lowers your points by {r:g}.
- Each token in the group account pays you {r:g} points and does not change any other member's points.
- Every round, every member also receives {base:g} points, whatever anyone does.""",
}
TEXT = """You are one of {size} members of a group that stays together for {rounds} rounds.

Every round, all members act at the same time: each receives {tokens} tokens and splits them between their own \
account and the group account, using the split tool once.
{accounts}

After each round you learn how many tokens the group account received in total and how many points you got. You \
never learn what any other member did."""

TOOL = {
    'name': 'split',
    'description': f'How many of your {TOKENS} tokens go to the group account; the rest go to your own account.',
    'strict': True,
    'input_schema': {
        'type': 'object',
        'additionalProperties': False,
        'required': ['group'],
        'properties': {'group': {'type': 'integer', 'description': f'From 0 to {TOKENS}.'}},
    },
}


def points(group, r):
    """Each member's points for a round, from the tokens each put in the group account."""
    total = sum(group.values())
    return {seat: round(TOKENS - g + r * total, 2) for seat, g in group.items()}


def instructions(level, wording):
    r = RETURNS[level]
    accounts = ACCOUNTS[wording].format(r=r, base=round((SIZE - 1) * TOKENS * r, 2))
    return TEXT.format(size=SIZE, rounds=ROUNDS, tokens=TOKENS, accounts=accounts)


def turn(n, seat, rounds, r):
    """The message a member reads at the start of round n: the last round's outcome for it, nothing about others."""
    text = f'Round {n} of {ROUNDS}.'
    if rounds:
        last = rounds[-1]
        text += (
            f' Last round you put {last[seat]} tokens in the group account, it received {sum(last.values())} in '
            f'total, and you got {points(last, r)[seat]:g} points.'
        )
    return text


def parse(reply):
    return agents.one_call(reply, 'split', 'group', lambda value: type(value) is int and 0 <= value <= TOKENS)


def contribution(rounds):
    """Share of tokens put in the group account, per round."""
    return [sum(r.values()) / (SIZE * TOKENS) for r in rounds]


def play_game(seed, level, wording, cap, model):
    """Ten rounds with one group. An invalid split counts as doing nothing: all 20 tokens stay in the own account."""
    text, r, name = instructions(level, wording), RETURNS[level], f'goods-{level}-{wording}-{seed:03d}'
    residents = {seat: agents.Resident(model, text, TOOL) for seat in SEATS}
    rounds, calls = [], []

    def one(seat, n):
        group, record = residents[seat].act(turn(n, seat, rounds, r), parse)
        charge(name, record['usd'])
        calls.append({'resident': seat, 'day': n} | record)
        return group or 0

    try:
        for n in range(1, ROUNDS + 1):
            check(cap)
            with ThreadPoolExecutor(SIZE) as pool:  # moves are simultaneous, so the calls can be too
                rounds.append(dict(zip(SEATS, pool.map(one, SEATS, [n] * SIZE))))
        status, error = 'complete', None
    except BaseException as e:  # noqa: BLE001 - any failure, an interrupt included, is recorded, never retried
        status, error = 'failed', f'{type(e).__name__}: {e}'
    return {
        'experiment': 'goods',
        'seed': seed,
        'level': level,
        'wording': wording,
        'model': agents.MODEL,
        'settings': agents.SETTINGS,
        'text': text,
        'status': status,
        'error': error,
        'usd': sum(c['usd'] for c in calls),
        'rounds': rounds,
        'calls': sorted(calls, key=lambda c: (c['day'], c['resident'])),
    }


def run(tag, seeds, cap):
    """Play every cell for each seed, seed by seed. Recorded games are skipped."""
    model = agents.chat()
    for seed in seeds:
        for level in RETURNS:
            for wording in WORDINGS:
                path = game_path(tag, 'goods', (level, wording), seed)
                if record(path, cap, play_game, seed, level, wording, cap, model):
                    return
