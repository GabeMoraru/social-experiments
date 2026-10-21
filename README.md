# Rations

**Do language-model agents respond to the stakes or to the story, and do they do it the way people did?**

Three experiments, each a copy of a published human study, so every result has a human answer beside it. In each, a
*stakes* variable changes what happens and a *story* variable changes only the wording, or, in the first, only the
game's name. If behaviour follows the stakes, the agents respond to consequences; if it follows the wording, they are
playing a part. All residents are copies of one model (`claude-haiku-5-5`) with fixed settings, and no text ever
tells them what to want.

| Experiment | Copies | What varies | People |
|---|---|---|---|
| **Name of the Game** | Ellingsen, Johannesson, Mollerstrom & Munkhammar 2012 | the game's name (Community / Stock Market) × the other side (a resident / a computer) | the name moves choices against a person (26% → 45% choose A), not against a computer (27% → 29%) |
| **Public goods** | Fehr & Gächter 2000; Isaac & Walker 1988; Andreoni 1995 | return per token (0.3 / 0.75) × wording (helping / harming, identical payoffs) | more is given at the higher return, giving falls over ten rounds, and harm wording halves it (34% → 16%) |
| **Rations** | the common-pool request game of Budescu, Rapoport & Suleiman 1990–92, with residents who can starve | scarcity (Plenty / Exact / Short) × framing (a village where you die / a game where you are out) | on the first claim, people ask for 1.13–1.26 equal shares |

Status: the code is complete and tested; the pilots and main runs have not been played.

## The rules

**Name of the Game.** One decision, once. Each resident chooses A or B at the same time as the other side: both A
pays 50 each, both B 20 each, and A against B pays 5 to the one who chose A and 80 to the other. Against another
resident, both choose; against a computer, the computer chooses A as often as residents did in the first arm, and
its points go to a receiver who makes no choice.

**Public goods.** Four residents, ten rounds, the same group throughout, no messages. Each round each receives 20
tokens and splits them between its own account (1 point a token) and the group account (the return, 0.3 or 0.75, to
every member per token). After each round it learns the group account's total and its own points, never what the
others did. The harm wording, Andreoni's, tells the same payoffs another way: a token kept pays 1 and costs every
other member the return, a token in the group account pays only its owner the return, and everyone gets a fixed
amount.

**Rations.** Six residents share a storehouse through five winter nights. It starts with 6 rations. Each day every
living resident, at the same time, may say one message to everyone (read the next morning), claim rations and give
rations to others. Then a delivery arrives, from a range every resident knows (7–11 at Plenty, 4–8 at Exact, 2–6 at
Short), and the claims are shared out of the storehouse, delivery included, in whole rations and in proportion if
they exceed it. Each night every resident
eats one of its own rations, or one from the storehouse by lot, and a resident who gets none dies. Doing nothing
never starves anyone while food suffices, so every avoidable death traces back to someone's claim.

[docs/decisions.md](docs/decisions.md) explains each rule and every departure from the human studies.

## Measures

All computed exactly from recorded moves, with the game as the unit.

- **Name of the Game:** the share choosing A.
- **Public goods:** the share of tokens put in the group account, per round and over the game.
- **Rations:**
  - **over-claiming**, keeping more than your need for the nights left (the primary outcome);
  - **avoidable deaths**, deaths that nobody claiming that day would have prevented;
  - withholding, rescue and self-sacrifice;
  - **grab advantage** at Short: survival of residents who kept more than an equal share of a contested store;
  - **day-1 claims** per expected equal share, set against the human request game.

Two judges label the *reasons* in the residents' thinking summaries, including whether a resident recognises a known
game or study: Jev, a hosted classifier, and an LLM judge from another provider than the players (`gpt-6-luna`).
Each is reported only where it holds up on held-out reference labels. [docs/analysis-plan.md](docs/analysis-plan.md)
is the pre-registered plan.

## Run it

```bash
uv sync
uv run rations report --tag main     # rebuild every table and chart from the recordings: free, no key
uv run pytest                        # the rules and measures, checked with scripted residents
```

Paid commands need `ANTHROPIC_API_KEY` (plus `OPENAI_API_KEY` and `TYPESAFE_API_KEY` for the judges), and each
takes `--cap`, a spend ceiling in USD. Every call is charged to `results/spend.jsonl`, and nothing is sent once it
reaches the cap.

```bash
uv run rations play label --tag pilot --seeds 1000:1005 --cap 1    # residents first, then the computer arm
uv run rations play goods --tag pilot --seeds 1000:1002 --cap 1
uv run rations play rations --tag pilot --seeds 1000:1002 --cap 1
uv run rations probe --cap 1                                        # can the model do Rations' arithmetic?
uv run rations judge luna --tag pilot --cap 1                       # LLM judge on thinking summaries
uv run rations judge jev --tag pilot --cap 1                        # classifier on the same summaries
uv run rations calibrate --tag pilot                                # sample for reference labels, then thresholds
```

At list price with `claude-haiku-5-5`, a game costs about $0.0005 (Name of the Game), $0.005 (Public goods) and $0.02
(Rations).

## Layout

```
src/rations/
  label.py     Name of the Game: payoffs, text, the choose tool, the two arms
  goods.py     Public goods: payoffs in both wordings, text, the split tool, the rounds
  game.py      Rations' rules, as plain functions; no model
  agents.py    one chat model per resident, kept as one conversation; Rations' text and act tool
  run.py       the spend ledger, one recording per game, Rations' loop, the comprehension probe
  metrics.py   Rations' measures, from a recording
  judge.py     reasons from thinking summaries: two judges, checked against reference labels
  report.py    tables, contrasts beside the human effects, and charts
  cli.py       the command line
tests/         rules, payoffs, texts, measures, calibration and the report, all offline
results/       recordings (results/<tag>/<experiment>/, one JSON per game), the spend ledger, the report
docs/          decisions and the analysis plan
```
