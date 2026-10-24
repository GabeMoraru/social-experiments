"""The results, rebuilt from recordings alone: no model, no key, no cost.

Writes results/<tag>/report.md, with a section for each experiment played in the tag, and its charts. The analysis
follows docs/analysis-plan.md: the game is the unit, seeds pair the cells, and each experiment's two primary
contrasts get paired bootstrap 97.5% intervals, shown beside the effect in the human study the experiment copies.
"""

import json
import math
import random
from collections import defaultdict
from statistics import mean

import matplotlib.pyplot as plt

from social_experiments import goods, judge, label
from social_experiments.agents import FRAMINGS
from social_experiments.game import LEVELS
from social_experiments.metrics import measure
from social_experiments.run import RESULTS, load

COLUMNS = (
    'over_claim_rate',
    'avoidable_deaths',
    'deaths',
    'withholding',
    'rescue',
    'self_sacrifice',
    'day1_claim_share',
    'day1_over_mean',
)
RESAMPLES = 10_000
# The human effects each contrast is set against, from the studies the experiments copy (see docs/analysis-plan.md).
PEOPLE = {
    'Stakes: Short - Plenty': 'no single human sign: scarcity raises extraction in some studies, lowers it in others',
    'Story: survival - game': 'not measured in people with these rules',
    'Name, residents: Community - Stock Market': '+0.185 (26.4% to 44.9%; Ellingsen et al. 2012)',
    'Name, residents minus name, computer': '+0.166 (the name moved the computer arm by +0.019 only)',
    'Return: 0.75 - 0.3': 'about +0.38 (about 12% to 50% in groups of 4; Isaac & Walker 1988, Figure II)',
    'Wording: positive - negative': '+0.174 (33.6% to 16.2%, at a return of 0.5; Andreoni 1995)',
}


def interval(values):
    """Mean and paired bootstrap 97.5% interval (two primary contrasts per experiment, Bonferroni)."""
    rng = random.Random(0)
    means = sorted(mean(rng.choices(values, k=len(values))) for _ in range(RESAMPLES))
    return mean(values), means[int(0.0125 * RESAMPLES)], means[int(0.9875 * RESAMPLES) - 1]


def seeds(games, cell, value, cells):
    """Each seed's value per cell, over the seeds with a complete game and a value in every one of the cells."""
    by_seed = defaultdict(dict)
    for g in games:
        if g['status'] == 'complete' and (v := value(g)) is not None:
            by_seed[g['seed']][cell(g)] = v
    return [c for c in by_seed.values() if len(c) == cells]


def contrasts(full, effects):
    """Report lines for each named contrast, computed per seed over the complete seeds."""
    out = [f'### Primary contrasts ({len(full)} complete seeds)', '']
    for name, effect in effects.items():
        values = [effect(c) for c in full]
        if len(values) >= 2:
            m, lo, hi = interval(values)
            out.append(f'- {name}: {m:+.3f}, 97.5% interval [{lo:+.3f}, {hi:+.3f}]. People: {PEOPLE[name]}.')
        else:
            out.append(f'- {name}: needs at least two complete seeds. People: {PEOPLE[name]}.')
    return out


def grab_advantage(games):
    """At Short: share surviving among residents who grabbed at least once, and among those who never did."""
    rows = []
    for frame in FRAMINGS:
        residents = [
            r for g in games if g['level'] == 'short' and g['framing'] == frame for r in g['measures']['residents']
        ]
        grabbed = [alive for grab, alive in residents if grab]
        restrained = [alive for grab, alive in residents if not grab]
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


def reasons(tag, calibration):
    """Share of summaries asserting each reason, per experiment and cell and judge, for the questions it passed."""
    jev, luna = judge.answers(), judge.answers(judge.LUNA_CACHE)
    columns = {
        f'{q} (Jev)': (jev, lambda a, q=q, t=c['threshold']: a[q] >= t) for q, c in calibration.items() if c['reported']
    }
    columns |= {f'{q} (Luna)': (luna, lambda a, q=q: a[q]) for q, c in calibration.items() if c['luna_reported']}
    shares = defaultdict(lambda: defaultdict(list))
    for key, text in judge.summaries(tag):
        experiment, game = key.split('/')[:2]
        cell = (experiment, *game.split('-')[:2])
        for column, (known, says_yes) in columns.items():
            if judge.digest(text) in known:
                shares[cell][column].append(says_yes(known[judge.digest(text)]))
    return shares, list(columns)


def chart(cells, path):
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 3.6))
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
        top = max((v for row in grid for v in row if not math.isnan(v)), default=0)
        for i, row in enumerate(grid):
            for j, value in enumerate(row):
                # white on the darker half of the colour scale, so every value stays readable
                ax.text(j, i, f'{value:.2f}', ha='center', va='center', color='white' if value > top / 2 else 'black')
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def rations_section(tag, games):
    for g in games:
        g['measures'] = measure(g['days'], g['level']) if g['status'] == 'complete' else None
    done = [g for g in games if g['measures']]
    cells = defaultdict(lambda: defaultdict(list))
    for g in done:
        for column in COLUMNS:
            cells[g['level'], g['framing']][column].append(g['measures'][column])
    out = [
        '## Rations',
        '',
        '![grid](grid.png)',
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
    out += [
        '',
        (
            'Day 1 is the human request game: one simultaneous claim each on a pool of known range, before any message. '
            'People there ask for 1.13 equal shares when the pool is certain and 1.26 when it may be 25% either way, and '
            'the group asks for more than the mean pool on 46% and 54% of trials (Rapoport et al. 1992).'
        ),
        '',
    ]
    full = seeds(done, lambda g: (g['level'], g['framing']), lambda g: g['measures']['over_claim_rate'], 6)
    out += contrasts(
        full,
        {
            'Stakes: Short - Plenty': lambda c: mean(c['short', f] - c['plenty', f] for f in FRAMINGS),
            'Story: survival - game': lambda c: mean(c[lv, 'survival'] - c[lv, 'game'] for lv in LEVELS),
        },
    )
    out += [
        '',
        '### Grab advantage at Short (share surviving)',
        '',
        '| Framing | Grabbed | Survived | Never grabbed | Survived |',
        '|---|---|---|---|---|',
    ]
    for frame, n_grab, grab, n_rest, rest in grab_advantage(done):
        out.append(
            f'| {frame} | {n_grab} | {"-" if grab is None else f"{grab:.2f}"} | {n_rest} | '
            f'{"-" if rest is None else f"{rest:.2f}"} |'
        )
    probe = RESULTS / 'probe.jsonl'
    if probe.exists():
        rows = [json.loads(line) for line in probe.read_text().splitlines()]
        right = sum(r['answer'] == r['expected'] for r in rows)
        out += ['', f'Comprehension probe: {right} of {len(rows)} answers correct.']
    chart(cells, RESULTS / tag / 'grid.png')
    return out


def label_section(games):
    out = [
        '## Name of the Game',
        '',
        '| Name | Other side | Games | Share choosing A | Invalid choices |',
        '|---|---|---|---|---|',
    ]
    for name in label.LABELS:
        for opponent in label.OPPONENTS:
            cell = [g for g in games if (g['label'], g['opponent'], g['status']) == (name, opponent, 'complete')]
            share = label.share_a(cell)
            invalid = sum(c is None for g in cell for c in g['choices'].values())
            out.append(
                f'| {name} | {opponent} | {len(cell)} | {"-" if share is None else f"{share:.2f}"} | {invalid} |'
            )
    out.append('')
    full = seeds(games, lambda g: (g['label'], g['opponent']), lambda g: label.share_a([g]), 4)

    def named(c, opponent):
        return c['community', opponent] - c['stock_market', opponent]

    return out + contrasts(
        full,
        {
            'Name, residents: Community - Stock Market': lambda c: named(c, 'resident'),
            'Name, residents minus name, computer': lambda c: named(c, 'resident') - named(c, 'computer'),
        },
    )


def goods_section(tag, games):
    done = [g for g in games if g['status'] == 'complete']
    out = [
        '## Public goods',
        '',
        '![rounds](goods.png)',
        '',
        '| Return | Wording | Games | Mean share to the group | Round 1 | Round 10 |',
        '|---|---|---|---|---|---|',
    ]
    fig, ax = plt.subplots(figsize=(6, 3.6))
    for level, r in goods.RETURNS.items():
        for wording in goods.WORDINGS:
            cell = [goods.contribution(g['rounds']) for g in done if (g['level'], g['wording']) == (level, wording)]
            if not cell:
                out.append(f'| {r} | {wording} | 0 | - | - | - |')
                continue
            by_round = [mean(c[n] for c in cell) for n in range(goods.ROUNDS)]
            out.append(
                f'| {r} | {wording} | {len(cell)} | {mean(by_round):.2f} | {by_round[0]:.2f} | {by_round[-1]:.2f} |'
            )
            ax.plot(range(1, goods.ROUNDS + 1), by_round, marker='o', label=f'return {r}, {wording}')
    ax.set(xlabel='Round', ylabel='Share of tokens to the group account', ylim=(0, 1))
    ax.set_xticks(range(1, goods.ROUNDS + 1))
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(RESULTS / tag / 'goods.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    out += [
        '',
        (
            'People decline over ten rounds: about 35% to 5% at a return of 0.3 and 55% to 31% at 0.75 (Isaac & Walker '
            '1988, Figure II); 47.5% to 20.9% in positive wording and 27.8% to 1.0% in negative (Andreoni 1995).'
        ),
        '',
    ]
    full = seeds(done, lambda g: (g['level'], g['wording']), lambda g: mean(goods.contribution(g['rounds'])), 4)
    return out + contrasts(
        full,
        {
            'Return: 0.75 - 0.3': lambda c: mean(c['high', w] - c['low', w] for w in goods.WORDINGS),
            'Wording: positive - negative': lambda c: mean(
                c[lv, 'positive'] - c[lv, 'negative'] for lv in goods.RETURNS
            ),
        },
    )


def report(tag):
    played = {experiment: load(tag, experiment) for experiment in ('rations', 'label', 'goods')}
    games = [g for experiment in played.values() for g in experiment]
    out = [
        f'# Results: {tag}',
        '',
        (
            f'{len(games)} games, {sum(g["status"] != "complete" for g in games)} failed, '
            f'{sum(bool(c["problem"]) for g in games for c in g["calls"])} invalid replies, '
            f'${sum(g["usd"] for g in games):.2f} at list price.'
        ),
    ]
    if played['rations']:
        out += [''] + rations_section(tag, played['rations'])
    if played['label']:
        out += [''] + label_section(played['label'])
    if played['goods']:
        out += [''] + goods_section(tag, played['goods'])
    calibration = json.loads(judge.THRESHOLDS.read_text()) if judge.THRESHOLDS.exists() else {}
    if calibration:
        out += [
            '',
            "## Judge agreement (Cohen's kappa)",
            '',
            'Against the reference labels on the held-out half, and between the two judges over every summary both read.',
            '',
            '| Question | Luna vs reference | Jev vs reference | Luna vs Jev | Reference passes agree |',
            '|---|---|---|---|---|',
        ]
        out += [
            f'| {q} | {c["luna_kappa"]:.2f} | {c["jev_kappa"]:.2f} | {c["luna_jev_kappa"]:.2f} | {c["pass_agreement"]:.2f} |'
            for q, c in calibration.items()
        ]
    shares, questions = reasons(tag, calibration)
    if questions:
        out += [
            '',
            '## Reasons in thinking summaries (share of replies)',
            '',
            '| Experiment | Cell | ' + ' | '.join(questions) + ' |',
            '|---' * (2 + len(questions)) + '|',
        ]
        for cell in sorted(shares):
            out.append(
                f'| {cell[0]} | {" ".join(cell[1:])} | '
                + ' | '.join(f'{mean(shares[cell][q]):.2f}' if shares[cell][q] else '-' for q in questions)
                + ' |'
            )
    (RESULTS / tag / 'report.md').write_text('\n'.join(out) + '\n')
    print('\n'.join(out))
