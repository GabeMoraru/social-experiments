"""The results, rebuilt from recordings alone: no model, no key, no cost.

Writes results/<tag>/report.md and results/<tag>/grid.png. The analysis follows docs/analysis-plan.md: the game is
the unit, seeds pair the six cells, and the two primary contrasts get paired bootstrap 97.5% intervals.
"""

import json
import random
from collections import defaultdict
from statistics import mean

import matplotlib.pyplot as plt

from rations import judge
from rations.agents import FRAMINGS
from rations.game import LEVELS
from rations.metrics import measure
from rations.run import RESULTS

COLUMNS = ('over_claim_rate', 'avoidable_deaths', 'deaths', 'withholding', 'rescue', 'self_sacrifice')
RESAMPLES = 10_000


def load(tag):
    """Every recorded game, with measures for the complete ones. Failed games are counted, never averaged in."""
    games = [json.loads(p.read_text()) for p in sorted((RESULTS / tag).glob('*.json'))]
    for g in games:
        g['measures'] = measure(g['days']) if g['status'] == 'complete' else None
    return games


def interval(values):
    """Mean and paired bootstrap 97.5% interval (two primary contrasts, Bonferroni)."""
    rng = random.Random(0)
    means = sorted(mean(rng.choices(values, k=len(values))) for _ in range(RESAMPLES))
    return mean(values), means[int(0.0125 * RESAMPLES)], means[int(0.9875 * RESAMPLES) - 1]


def contrasts(games):
    """Stakes (Short minus Plenty) and story (survival minus game) in over-claiming, per seed, over complete pairs."""
    by_seed = defaultdict(dict)
    for g in games:
        by_seed[g['seed']][g['level'], g['framing']] = g['measures']['over_claim_rate']
    full = [cells for cells in by_seed.values() if len(cells) == len(LEVELS) * len(FRAMINGS)]
    stakes = [mean(c['short', f] - c['plenty', f] for f in FRAMINGS) for c in full]
    story = [mean(c[lv, 'survival'] - c[lv, 'game'] for lv in LEVELS) for c in full]
    return len(full), stakes, story


def grab_advantage(games):
    """At Short: share surviving among residents who over-claimed at least once, and among those who never did."""
    rows = []
    for frame in FRAMINGS:
        residents = [
            r for g in games if g['level'] == 'short' and g['framing'] == frame for r in g['measures']['residents']
        ]
        grabbed = [alive for over, alive in residents if over]
        restrained = [alive for over, alive in residents if not over]
        rows.append(
            (
                frame,
                len(grabbed),
                mean(grabbed) if grabbed else None,
                len(restrained),
                mean(restrained) if restrained else None,
            )
        )
    return rows


def reasons(tag):
    """Share of summaries asserting each reported reason, per cell. Empty until calibration has run."""
    if not judge.THRESHOLDS.exists():
        return {}, []
    thresholds = {q: t['threshold'] for q, t in json.loads(judge.THRESHOLDS.read_text()).items() if t['reported']}
    known, shares = judge.answers(), defaultdict(lambda: defaultdict(list))
    for key, text in judge.summaries(tag):
        cell = tuple(key.split('/')[0].split('-')[:2])
        for q, t in thresholds.items():
            if judge.digest(text) in known:
                shares[cell][q].append(known[judge.digest(text)][q] >= t)
    return shares, list(thresholds)


def chart(cells, path):
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    for ax, column, title in zip(
        axes,
        ('over_claim_rate', 'avoidable_deaths'),
        ('Over-claiming (share of resident-days)', 'Avoidable deaths per game'),
    ):
        grid = [
            [mean(cells[lv, f][column]) if cells[lv, f][column] else float('nan') for f in FRAMINGS] for lv in LEVELS
        ]
        ax.imshow(grid, cmap='Reds', vmin=0)
        ax.set_xticks(range(len(FRAMINGS)), [f.capitalize() for f in FRAMINGS])
        ax.set_yticks(range(len(LEVELS)), [lv.capitalize() for lv in LEVELS])
        ax.set_title(title, fontsize=10)
        for i, row in enumerate(grid):
            for j, value in enumerate(row):
                ax.text(j, i, f'{value:.2f}', ha='center', va='center')
    fig.tight_layout()
    fig.savefig(path, dpi=150)


def report(tag):
    games = load(tag)
    done = [g for g in games if g['measures']]
    cells = defaultdict(lambda: defaultdict(list))
    for g in done:
        for column in COLUMNS:
            cells[g['level'], g['framing']][column].append(g['measures'][column])
    out = [
        f'# Results: {tag}',
        '',
        (
            f'{len(games)} games, {sum(g["status"] != "complete" for g in games)} failed, '
            f'{sum(bool(c["problem"]) for g in games for c in g["calls"])} invalid acts, '
            f'${sum(g["usd"] for g in games):.2f} at list price.'
        ),
        '',
        '![grid](grid.png)',
        '',
        '## Per cell (means per complete game)',
        '',
        '| Scarcity | Framing | Games | ' + ' | '.join(COLUMNS) + ' |',
        '|---' * (3 + len(COLUMNS)) + '|',
    ]
    for lv in LEVELS:
        for f in FRAMINGS:
            values = cells[lv, f]
            n = len(values['deaths'])
            out.append(
                f'| {lv} | {f} | {n} | ' + ' | '.join(f'{mean(values[c]):.2f}' if n else '-' for c in COLUMNS) + ' |'
            )
    pairs, stakes, story = contrasts(done)
    out += ['', f'## Primary contrasts (over-claiming, {pairs} complete seeds)', '']
    for name, values in (('Stakes: Short - Plenty', stakes), ('Story: survival - game', story)):
        if len(values) >= 2:
            m, lo, hi = interval(values)
            out.append(f'- {name}: {m:+.3f}, 97.5% interval [{lo:+.3f}, {hi:+.3f}]')
        else:
            out.append(f'- {name}: needs at least two complete seeds')
    out += [
        '',
        '## Grab advantage at Short (share surviving)',
        '',
        '| Framing | Over-claimers | Survived | Never over-claimed | Survived |',
        '|---|---|---|---|---|',
    ]
    for frame, n_grab, grab, n_rest, rest in grab_advantage(done):
        out.append(
            f'| {frame} | {n_grab} | {"-" if grab is None else f"{grab:.2f}"} | {n_rest} | '
            f'{"-" if rest is None else f"{rest:.2f}"} |'
        )
    shares, questions = reasons(tag)
    if questions:
        out += [
            '',
            '## Reasons in thinking summaries (share of replies)',
            '',
            '| Scarcity | Framing | ' + ' | '.join(questions) + ' |',
            '|---' * (2 + len(questions)) + '|',
        ]
        for lv in LEVELS:
            for f in FRAMINGS:
                out.append(
                    f'| {lv} | {f} | '
                    + ' | '.join(f'{mean(shares[lv, f][q]):.2f}' if shares[lv, f][q] else '-' for q in questions)
                    + ' |'
                )
    probe = RESULTS / 'probe.jsonl'
    if probe.exists():
        rows = [json.loads(line) for line in probe.read_text().splitlines()]
        right = sum(r['answer'] == r['expected'] for r in rows)
        out += ['', '## Comprehension probe', '', f'{right} of {len(rows)} answers correct.']
    chart(cells, RESULTS / tag / 'grid.png')
    (RESULTS / tag / 'report.md').write_text('\n'.join(out) + '\n')
    print('\n'.join(out))
