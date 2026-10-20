# Decisions

Each rule exists to answer the question cleanly. This records why.

## The game

- **No goal sentence.** Residents are told the situation and its consequences, never what to want. In
  [Handshake Island](https://github.com/GabeMoraru/handshake-island), earlier work with model agents, one goal sentence ("Your score is all that counts.") moved promise-keeping several-fold, which
  would swamp the effects measured here.
- **Doing nothing is safe where food suffices.** Every night a resident eats its own ration, or one from the
  storehouse. Without this, a resident that forgets to claim would starve even at Plenty, and the measures would
  record a mistake as a choice. Now every death at Plenty needs someone else's claim.
- **Simultaneous moves.** In resource games with sequential requests, early movers take more (Budescu, Rapoport &
  Suleiman 1992). Moving together removes turn order as a cause of death.
- **Proportional split of contested claims.** Claiming more always wins a larger share, so grabbing pays off for the
  grabber. Without a payoff, the game could only measure kindness.
- **Uncertain deliveries, and no points.** The only reason to grab is fear of going hungry. Uncertainty about a shared
  resource reliably raises requests in people (Budescu, Rapoport & Suleiman 1990). Points for spare rations would add
  greed, but they would be a goal sentence in another form.
- **Full information, arithmetic done.** Each day shows every resident's holdings and shortfall, so a miscount cannot
  pass for greed, and nobody can withhold without seeing who goes short.
- **A starting store of one night's food.** Nobody can starve before the first messages are read.
- **Six residents, five days.** Enough bystanders for withholding to be a real option (helping falls as the number of
  bystanders rises; Darley & Latané 1968), at 30 calls a game.

## The agents

- **One tool, `act`, and the whole conversation in context.** A memory or retrieval tool would make a death possibly
  "forgot to look", and every extra action changes what seems expected (adding a take option lowers giving; List 2007).
- **Fixed model settings**: adaptive thinking with readable summaries, medium effort, tool choice left to the model,
  one call per turn. Never varied. The conversation is append-only, and block binding makes any edit fail loudly.
- **Invalid output is not retried.** A reply without one valid `act` call means doing nothing that day. Failed
  requests are retried by the SDK (they produce no reply); a reply is never asked for twice.

## The study

- **Two variables, one model.** Scarcity × framing is the question (stakes or story). Model, oversight and alternate
  rule wordings were left out to keep each cell large and the result one chart. A naming effect has human precedent:
  the same dilemma called the "Wall Street" rather than the "Community" game draws much less cooperation (Liberman,
  Samuels & Ross 2004).
- **Measures from moves, reasons from a judge.** Everything about what residents did is computed exactly; a
  classifier only labels why, and only where its thresholds hold on held-out labels.
- **Avoidable means someone held spare.** A death counts as avoidable only when others held more than their own need
  that night. Deaths from a run of low deliveries are bad luck, not harm.
- **Everything is recorded.** Each game keeps every request text, reply, thinking summary, token count and cost, so
  every number can be recomputed without a model call.
