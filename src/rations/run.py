"""Running games: the loop, the spend cap and one recording per game.

Every paid call is charged to one append-only ledger, and nothing is sent once the ledger reaches the cap. A game
that fails is recorded with its error and kept; it is never retried, and a run never repeats a recorded game.
"""

import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from rations import agents, game

RESULTS = Path('results')
LEDGER = RESULTS / 'spend.jsonl'
BUDGET = 21.50  # USD at list price for the whole project. Never raised.
_ledger_lock = threading.Lock()


class OverBudget(RuntimeError):
    pass


def spent():
    if not LEDGER.exists():
        return 0.0
    return sum(json.loads(line)['usd'] for line in LEDGER.read_text().splitlines())


def charge(what, usd):
    with _ledger_lock:
        LEDGER.parent.mkdir(exist_ok=True)
        with LEDGER.open('a') as f:
            f.write(json.dumps({'time': time.strftime('%Y-%m-%dT%H:%M:%S'), 'what': what, 'usd': usd}) + '\n')


def check(cap):
    limit = min(cap, BUDGET)
    if spent() >= limit:
        raise OverBudget(f'spent ${spent():.2f} of a ${limit:.2f} cap')


def game_path(tag, experiment, cell, seed):
    return RESULTS / tag / experiment / f'{"-".join(cell)}-{seed:03d}.json'


def load(tag, experiment):
    """Every recorded game of one experiment in a tag."""
    return [json.loads(p.read_text()) for p in sorted((RESULTS / tag / experiment).glob('*.json'))]


def record(path, cap, play, *args):
    """Play one game, play(*args), unless it is already recorded, and write its recording. Returns whether the run
    must stop."""
    if path.exists():
        return False
    check(cap)
    recording = play(*args)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(recording, indent=1))
    error = recording['error']
    print(
        f'{path.parent.name}/{path.name}: {recording["status"]}, ${recording["usd"]:.4f}, total ${spent():.2f}'
        + (f' ({error})' if error else '')
    )
    return bool(error) and error.startswith(('OverBudget', 'KeyboardInterrupt'))


def play_game(seed, level, frame, cap, model):
    """Play one game with six model residents and return its recording."""
    seats = game.seating(seed)
    residents = {
        name: agents.Resident(model, agents.rules(frame, level, name, seats), agents.act_tool(frame)) for name in seats
    }
    calls, progress = [], {}
    label = f'{level}-{frame}-{seed:03d}'

    def one(name, morning, days):
        act, record = residents[name].act(agents.turn(frame, level, name, morning, days), agents.parse)
        charge(label, record['usd'])
        calls.append({'resident': name, 'day': morning['day']} | record)
        return act

    def decide(day, morning, days):
        progress['days'] = days  # the game's own list, so a failed game still keeps the days it finished
        check(cap)  # a day costs about a cent, so the cap is passed by one day's calls at most
        with ThreadPoolExecutor(len(morning['alive'])) as pool:  # moves are simultaneous, so the calls can be too
            acts = list(pool.map(lambda name: one(name, morning, days), morning['alive']))
        return dict(zip(morning['alive'], acts))

    recording = {
        'experiment': 'rations',
        'seed': seed,
        'level': level,
        'framing': frame,
        'model': agents.MODEL,
        'settings': agents.SETTINGS,
        'seating': seats,
        'deliveries': game.deliveries(seed, level),
        'rules': agents.rules(frame, level, '{me}', seats),
    }
    try:
        days, status, error = game.play(seed, level, decide), 'complete', None
    except BaseException as e:  # noqa: BLE001 - any failure, an interrupt included, is recorded, never retried
        days, status, error = progress.get('days', []), 'failed', f'{type(e).__name__}: {e}'
    return recording | {
        'status': status,
        'error': error,
        'usd': sum(c['usd'] for c in calls),
        'days': days,
        'calls': sorted(calls, key=lambda c: (c['day'], seats.index(c['resident']))),
    }


def run(tag, seeds, cap):
    """Play every Rations cell for each seed, seed by seed so pairs complete together. Recorded games are skipped."""
    model = agents.chat()
    for seed in seeds:
        for level in game.LEVELS:
            for frame in agents.FRAMINGS:
                path = game_path(tag, 'rations', (level, frame), seed)
                if record(path, cap, play_game, seed, level, frame, cap, model):
                    return


PROBE = """Suppose no {who} ever claims or gives anything, and every delivery is exactly {mean}. How many {whos} will \
{remain}? Work it out, then end your reply with "Answer: <number>"."""


def passive_survivors(level):
    """The probe's answer: everyone eats from the store, deliveries at their mean, the unfed are gone."""
    alive, store = len(game.NAMES), game.START_STORE
    for _ in range(game.DAYS):
        store += game.MEAN_DELIVERY[level]
        alive = min(alive, store)
        store -= alive
    return alive


def probe(reps, cap):
    """Ask whether the model can do the game's arithmetic, outside any game, so over-claiming isn't a miscount."""
    model, path = agents.chat(), RESULTS / 'probe.jsonl'
    for level in game.LEVELS:
        for frame in agents.FRAMINGS:
            f = agents.FRAMES[frame]
            question = PROBE.format(**f, mean=game.MEAN_DELIVERY[level])
            for rep in range(reps):
                check(cap)
                reply = model.invoke(
                    [SystemMessage(agents.rules(frame, level, 'Ada', game.NAMES)), HumanMessage(question)]
                )
                usd = agents.cost(reply.usage_metadata)
                charge(f'probe-{level}-{frame}', usd)
                found = re.findall(r'Answer:\s*(\d+)', reply.text)
                answer = int(found[-1]) if found else None
                row = {
                    'level': level,
                    'framing': frame,
                    'rep': rep,
                    'expected': passive_survivors(level),
                    'answer': answer,
                    'usd': usd,
                    'reply': reply.content,
                }
                with path.open('a') as out:
                    out.write(json.dumps(row) + '\n')
                print(f'probe {level}-{frame} #{rep}: answered {answer}, expected {row["expected"]}')
