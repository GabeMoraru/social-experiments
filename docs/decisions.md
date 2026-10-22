# Decisions

Each rule exists to answer the question cleanly. This records why, and every place an experiment departs from the
human study it copies.

## The study

- **Copies of human studies, not a new game.** A game invented for the study has no human result to compare
  against, and a reader must learn its rules first. Each experiment copies a published design, so each result sits
  beside a human one.
- **Stakes against story, in each experiment.** Each experiment crosses one variable that changes what happens with
  one that changes only the words. A naming effect has human precedent: the same dilemma called the "Wall Street"
  rather than the "Community" game draws much less cooperation (Liberman, Samuels & Ross 2004).
- **One model,** to keep each cell large. Cooperation varies many-fold across models (Affonso 2026), so the results
  are claims about this model only.
- **Direction first.** Across 156 replicated experiments, model main effects matched the human direction 73–81% of
  the time, while their sizes ran 2–3× larger (Cui, Li & Zhou 2024). So each effect's direction is compared with
  people's; sizes and levels are described.
- **The game is the unit.** Residents of one game are copies of one model, so treating them as independent people
  would overstate the evidence.

## Text residents read

- **No goal sentence.** Residents are told the situation and its consequences, never what to want; payoffs are
  stated as facts. In [Handshake Island](https://github.com/GabeMoraru/handshake-island), earlier work with model
  agents, one goal sentence ("Your score is all that counts.") moved promise-keeping several-fold, which would swamp
  the effects measured here.
- **The paradigm is never named,** and its usual words ("public good", "prisoner's dilemma", "cooperate", "free
  ride") never appear. Models answer differently when a classic study is named: in one study, conformity in the
  Asch paradigm went from 0% to 83% when it was (Bose 2026). Residents still often recognise the structure, so a judge
  question records it.
- **Residents are never told the others are copies of one model.** Telling them changes contributions in public
  goods games by up to 4 of 10 points (arXiv 2508.18467).
- **Framings differ only in wording.** One template per experiment, nouns only, with one exception: the public goods
  harm wording changes the sentences describing the payoffs, following Andreoni's, and a test checks the payoffs are
  identical.

## Name of the Game

- **Ellingsen et al. 2012, not Liberman et al. 2004.**
  - Liberman's game was small (48 players), seven rounds with one partner, and mixes in reputation.
  - Ellingsen's is one-shot, simultaneous and larger (about 112 per arm). It already has no goal sentence, and it
    has the computer control.
- **"Stock Market Game", not "Wall Street Game".** Ellingsen used it. It is also less famous, and Dreber et al.
  likewise swapped "Wall Street" for "Profit".
- **The computer control.** In people the name's effect disappears when a computer chooses for the other side, so
  the name works through expectations of the other player. A model whose name effect survives against the computer
  is playing the part the name suggests.
  - The computer copies the resident arm's share of A, as Ellingsen's copied people's, so that arm is played first.
- **Departures:**
  - points instead of kronor;
  - the lab procedure (raising hands, envelopes) cut;
  - "experiment" not used;
  - the payoffs given as four sentences rather than a matrix;
  - no payment.
- **No elicited beliefs.** Ellingsen notes that asking before the choice changes it and asking after is biased by
  it. Models' stated beliefs and actions also disagree (Lu et al. 2026).

## Public goods

- **Fehr & Gächter's no-punishment partner arm:** 4 members, 20 tokens, 10 rounds, the horizon known, fixed groups,
  no messages. After each round a member sees the group total and its own points, as in Isaac & Walker and Andreoni.
- **Returns of 0.3 and 0.75** are Isaac & Walker's low and high. They also varied the endowment by cell; here it is
  20 in every cell, a stated departure.
- **Andreoni's positive and negative wording, not give and take.** Positive against negative wording is the robust
  human effect (33.6% against 16.2%). Give against take shows no average effect (Cartwright 2016).
- **The same choice in both wordings.** Khadjavi & Lange (2015) found part of Andreoni's effect came from changing
  which actions were available. Here both wordings split the same 20 tokens between the same two accounts.
- **Andreoni's wording, closely paraphrased.** It keeps the own account paying 1 and the group account paying
  its owner the return, mirroring the positive wording.
- **Cut:** punishment, messages, group size, strangers matching.

## Rations

- **Doing nothing is safe where food suffices.** Every night a resident eats its own ration, or one from the
  storehouse. Without this, a resident that forgets to claim would starve even at Plenty, and the measures would
  record a mistake as a choice. Now every death at Plenty needs someone else's claim.
- **Simultaneous moves.** In resource games with sequential requests, early movers take more, even when earlier
  requests are hidden (Budescu, Rapoport & Suleiman 1992; Budescu, Suleiman & Rapoport 1995). Moving together
  removes turn order as a cause of death.
- **Claims before the delivery.** In the human request game the pool's size is uncertain when people ask, and
  requests rise with its range: from 113 to 172 per equal share of 100 (Rapoport et al. 1992). So residents claim
  first and the day's delivery arrives before claims are shared out. The text says plainly that claims are shared
  out of the store plus the delivery, in whole rations, and that what is not claimed stays in the store: without
  those words, pilot residents read claims as coming only from the morning's store and shares as fractions. Later
  days add uncertainty about future deliveries too, closer to growth-rate uncertainty, which also raises extraction
  (Hine & Gifford 1996; Roch & Samuelson 1997).
- **Proportional split of contested claims, a departure.** Under the human game's rule an over-request grants
  nothing to anyone; here everyone would then eat from the store, and harm would be nearly impossible. Proportional
  shares mean claiming more always wins more, so grabbing pays off for the grabber.
- **No points.** The only reason to grab is fear of going hungry. Points for spare rations would add greed, but they
  would be a goal sentence in another form.
- **Full information, arithmetic done, no anchor.** Each day shows every resident's holdings and the need for the
  nights left, so a miscount cannot pass for greed. In GovSim, accuracy at the arithmetic predicted survival (Piatti et al. 2024).
  - The holdings table shows no "short by N". People anchor requests on numbers on show (Budescu, Rapoport &
    Suleiman 1992), and that number would sit exactly at the over-claiming threshold.
- **A starting store of one night's food.** With the first delivery before the first night, nobody can starve
  before the first messages are read.
- **Six residents, five days.** The human games had five players. Six gives enough bystanders for withholding to be
  a real option (helping falls as the number of bystanders rises; Darley & Latané 1968), at 30 calls a game.
- **Scarcity has no single human sign.** Scarcity of the environment raises extraction in some resource dilemmas and
  lowers hostility in others, so the stakes contrast is reported against the day-1 human benchmark, not a predicted
  direction.

## The agents

- **One tool per experiment, and the whole conversation in context.** A memory or retrieval tool would make a death
  possibly "forgot to look", and every extra action changes what seems expected (adding a take option lowers giving;
  List 2007).
- **Fixed model settings**: adaptive thinking with readable summaries, medium effort, tool choice left to the model,
  one call per turn. Never varied. The conversation is append-only, and block binding makes any edit fail loudly.
- **Invalid output is not retried.** A reply without one valid tool call is recorded: doing nothing in Rations,
  keeping every token in Public goods, and neither A nor B in Name of the Game. Failed requests are retried by the
  SDK (they produce no reply); a reply is never asked for twice.

## Measures and judges

- **Measures from moves, reasons from judges.** Everything about what residents did is computed exactly; judges only
  label why, and only where they hold up on held-out labels.
- **Over-claiming stays Rations' primary outcome.** Its threshold, a resident's own need, is the same in every cell.
  A claim per equal share is not, since the same claim is a larger share of a smaller store. So that measure is used
  only for day 1 against people.
- **Grabbing counts taking your need from a contested store,** not only claims beyond need. At Short a resident
  that takes its full need on day 1 from a store that cannot meet every claim decides who dies.
- **Kept, not claimed.** Over-claiming and grabbing count a claim less what the resident gave away the same day: in
  the pilot, residents claimed rations in order to hand them out.
- **Avoidable means nobody claiming would have prevented it.** With no claims, the day's pool feeds everyone who
  holds nothing, as far as it goes; a death beyond that shortfall is someone's doing, and the rest are bad luck.
  Counting only spare beyond the survivors' remaining nights would miss a resident who grabs all five nights on day 1.
- **Two judges, one from another provider.** A classifier (Jev) and an LLM judge answer the same yes-or-no questions,
  so each checks the other. LLM judges favour their own model family (Spiliopoulou et al. 2025), so the judge comes
  from another provider than the players. It quotes its evidence before each verdict and never sees the condition.
- **A recognition question.** In a development game, a resident's reasoning began "This is a prisoner's dilemma
  setup". A model that recognises a classic study may reproduce its textbook answer, so recognition is labelled and
  reported per cell.
- **Everything is recorded.** Each game keeps every request text, reply, thinking summary, token count and cost, so
  every number can be recomputed without a model call.
