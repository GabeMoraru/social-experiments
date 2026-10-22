# Social experiments

Three published human experiments reimplemented as multi-agent environments for language models. Every seat is played
by `claude-haiku-5-5`; two judges from other providers label the reasoning; every table is recomputed offline from
the recordings.

Each experiment crosses a **stakes** variable (changes the payoffs or the rules) with a **story** variable (changes
only the wording, or only the game's name), and reports each effect's direction beside the human study's.

| Experiment | Source | Design | Calls per game | Measure |
|---|---|---|---|---|
| **Name of the Game** | Ellingsen, Johannesson, Mollerstrom & Munkhammar 2012 | name (Community / Stock Market) × other side (resident / computer), 60 seeds | 2 | share choosing A |
| **Public goods** | Fehr & Gächter 2000; Isaac & Walker 1988; Andreoni 1995 | return per token (0.3 / 0.75) × wording (positive / negative, identical payoffs), 40 seeds | 40 | share of tokens to the group account |
| **Rations** | request game of Budescu, Rapoport & Suleiman 1990–92, extended with starvation | scarcity (Plenty / Exact / Short) × framing (survival / game nouns), 40 seeds | ≤ 30 | over-claiming; avoidable deaths |

Main run: 640 games, 13,413 model calls, 10,547 thinking summaries, no failed games and no invalid replies, $5.24 at
list price. [results/main/report.md](results/main/report.md) has every table.

## Results

Pre-registered contrasts ([docs/analysis-plan.md](docs/analysis-plan.md)), paired by seed, with paired bootstrap
97.5% intervals (10,000 resamples, Bonferroni for two contrasts per experiment). The unit is the game.

| Experiment | Contrast | Model | People | Same direction |
|---|---|---|---|---|
| Name of the Game | Community − Stock Market, against a resident | +0.79 [+0.70, +0.88] | +0.185 | yes, about 4× larger |
| Name of the Game | the same, minus the effect against the computer | +0.78 [+0.69, +0.87] | +0.166 | yes |
| Public goods | return 0.75 − 0.3 | +0.36 [+0.28, +0.44] | about +0.38 | yes |
| Public goods | positive − negative wording | −0.22 [−0.29, −0.15] | +0.174 | **no** |
| Rations | Short − Plenty (over-claiming rate) | +0.058 [+0.043, +0.073] | no single sign | — |
| Rations | survival − game (over-claiming rate) | +0.037 [+0.027, +0.047] | not measured | — |

- **Name of the Game:** 97% A under "Community" and 18% under "Stock Market" against a resident; 1% and 0% against
  the computer. Nearly every resident-arm summary identifies the game as a prisoner's dilemma.
- **Public goods:** contributions fall to near zero by round 10 in every cell except 0.75 with negative wording,
  which ends at 27%.
- **Rations:** over-claiming is 1–11% of resident-days. Avoidable deaths per game:

  | | Survival | Game |
  |---|---|---|
  | Plenty | 0.28 | 0.00 |
  | Exact | 0.97 | 0.03 |
  | Short | 2.17 | 0.88 |

  Day-1 claims are 1.5–2.9 expected equal shares under survival nouns and 0.5–1.0 under game nouns (people:
  1.13–1.26). At Short under survival nouns, every resident that never grabbed died, against 35% of those that did.

## How it works

```
play ──▶ results/<tag>/<experiment>/<cell>-<seed>.json ──▶ metrics ──┐
                       │                                             ├──▶ report.md, charts
                       └──▶ thinking summaries ──▶ judges ──▶ caches ┘
                                                     ▲
                              reference labels ──▶ calibrate ──▶ thresholds.json
```

**Model calls.**
- LangChain `ChatAnthropic` with one fixed configuration for every call (`agents.SETTINGS`): adaptive thinking with
  summarized display, medium effort, 16k max tokens, tool choice auto, parallel tool calls off.
- Each resident is one append-only conversation (`agents.Resident`). Thinking blocks are bound to their prefix in
  error mode, so any edit to the history fails the request instead of passing silently.
- Each experiment exposes one strict-schema tool (`choose`, `split` or `act`). Its arguments are parsed as data and
  never executed. A reply that is not exactly one valid call is recorded with the reason and counts as doing nothing;
  it is never retried.
- Simultaneous moves run concurrently in a thread pool. Requests use prompt caching.

**Recordings.** One JSON file per game, written once, never updated:
`experiment`, `seed`, cell variables, `model`, `settings`, the full rules text, `status`, `error`, `usd`, the
per-day or per-round state (`days`, `rounds` or `choices`), and `calls`. Each call keeps the request text, the raw
reply content blocks (thinking included), `stop_reason`, token usage and cost. A failed game keeps its error and the
state it reached. Seed *k* gives the same deliveries, seating and lots in every cell, so cells pair by seed.

**Measures** are pure functions of a recording (`metrics.measure`, `label.share_a`, `goods.contribution`); the
report needs no API key.

**Spend.** Every call is priced at list rates and appended to `results/spend.jsonl`. Each command takes `--cap` (USD)
and nothing is sent once spend reaches it; the project total is capped at $21.50 (`run.BUDGET`). Recorded games
are skipped, so an interrupted run resumes.

**Judges.** Two judges answer five yes/no questions about each thinking summary: own survival, others' survival,
fairness, test awareness, and recognition of a known game or study.
- **Jev** (TypeSafe's classifier, pinned to `jev-1.13.0`, over REST) returns a probability per question.
- **Luna** (`gpt-6-luna`, OpenAI Responses API, strict JSON-schema output) quotes its evidence before each verdict.
  It is from another provider than the players and sees only the summary text.
- Answers are cached by the SHA-256 of the summary, eight requests at a time, so reruns only ask for new summaries.

**Calibration.** 200 summaries, drawn in turn from each experiment, were labelled in two independent blinded passes;
summaries both passes agree on are split in half by digest. Jev's threshold is the lowest reaching precision 0.9 on
one half and must hold on the other; Luna must reach Cohen's κ ≥ 0.6 on the held-out half.

| Question | Pass agreement | Jev held-out precision | Luna κ | Reported |
|---|---|---|---|---|
| recognition | 0.975 | 0.96 | 0.89 | both judges |
| fairness | 0.99 | — | 0.69 | Luna |
| others' survival | 0.97 | 0.57 | 0.65 | Luna |
| own survival | 0.935 | 0.50 | 0.33 | neither |
| test awareness | 1.00 | — | 0.00 | neither (no positives in the sample) |

## The rules

**Name of the Game.** One-shot, simultaneous A or B. Both A pay 50 each, both B 20 each, A against B pays 5 to A and
80 to B. Against a resident, both choose. Against the computer, it plays A at the rate observed in the resident arm
(so that arm runs first) and its points go to a passive receiver.

**Public goods.** Groups of four, ten rounds, fixed membership, no messages. Each round every member splits 20 tokens
between its own account (1 point per token) and the group account (the return, 0.3 or 0.75, to every member per
token), then sees the group total and its own points. The negative wording, after Andreoni, states the same payoffs
as a cost to others of each kept token plus a fixed payment; `tests/test_goods.py` checks the payoffs are identical.

**Rations.** Six residents, five days, a store starting at 6. Each day every living resident simultaneously sends one
broadcast message (read the next morning), claims rations and gives rations. Then a delivery arrives, uniform over a known range (7–11 Plenty,
4–8 Exact, 2–6 Short), and claims are filled from store plus delivery, proportionally in whole rations when they
exceed it. Each night every resident eats one of its own rations or one from the store by lot; one that gets none
dies. With no claims at all, nobody starves while food suffices, so each avoidable death is attributable to claims.

[docs/decisions.md](docs/decisions.md) gives the reason for each rule and every departure from the source studies.

## Run it

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run social-experiments report --tag main     # rebuild every table and chart from the recordings: free, no key
uv run pytest                                   # 30 offline tests with a scripted model
```

Paid commands need `ANTHROPIC_API_KEY` (plus `OPENAI_API_KEY` and `TYPESAFE_API_KEY` for the judges):

```bash
uv run social-experiments play label --tag pilot --seeds 1000:1005 --cap 1    # resident arm, then the computer arm
uv run social-experiments play goods --tag pilot --seeds 1000:1002 --cap 1
uv run social-experiments play rations --tag pilot --seeds 1000:1002 --cap 1
uv run social-experiments probe --cap 1                                        # Rations arithmetic check
uv run social-experiments judge luna --tag pilot --cap 1
uv run social-experiments judge jev --tag pilot --cap 1
uv run social-experiments calibrate --tag pilot                                # sample to label, then thresholds
```

At list price a game costs about $0.0003 (Name of the Game), $0.006 (Public goods) and $0.02 (Rations).

## Layout

```
src/social_experiments/
  label.py     Name of the Game: payoffs, text, the choose tool, the two arms
  goods.py     Public goods: payoffs in both wordings, text, the split tool, the rounds
  game.py      Rations' rules as plain functions; no model
  agents.py    model settings, the Resident conversation, Rations' text and act tool, pricing
  run.py       spend ledger, recording, Rations' game loop, the comprehension probe
  metrics.py   Rations' measures from a recording
  judge.py     both judges, the answer caches, calibration
  report.py    contrasts, bootstrap intervals, tables and charts
  cli.py       the command line
tests/         rules, payoffs, prompt text, measures, judges and the report, offline (CI: ruff and pytest)
results/       recordings (results/<tag>/<experiment>/), reports and charts, the spend ledger, the judges' answers,
               reference labels, thresholds and the probe
docs/          decisions and the pre-registered analysis plan
```

MIT licensed.
