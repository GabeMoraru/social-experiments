"""The rules, as plain functions over plain data. Nothing here calls a model.

Six residents share a storehouse for five days. Each day every living resident claims rations and gives rations at
the same time; then a delivery of uncertain size arrives and the claims are shared out of the storehouse; each night
every resident eats one of its own rations, or one from the storehouse, and a resident who gets neither dies.
"""

import random

NAMES = ('Ada', 'Ben', 'Cal', 'Dev', 'Eli', 'Fay')
DAYS = 5
START_STORE = 6  # one night's food: with the first delivery, nobody can starve before the first messages are read
SPREAD = 2  # a delivery is its level's mean plus or minus up to SPREAD, each value equally likely
MEAN_DELIVERY = {'plenty': 9, 'exact': 6, 'short': 4}
LEVELS = tuple(MEAN_DELIVERY)


def delivery_range(level):
    return MEAN_DELIVERY[level] - SPREAD, MEAN_DELIVERY[level] + SPREAD


def deliveries(seed, level):
    """The five deliveries. A seed draws the same offsets at every level, so paired games differ only in the mean."""
    rng = random.Random(f'deliveries {seed}')
    return [MEAN_DELIVERY[level] + rng.randint(-SPREAD, SPREAD) for _ in range(DAYS)]


def seating(seed):
    """The order residents are listed in, fixed within a game and shuffled across seeds."""
    names = list(NAMES)
    random.Random(f'seating {seed}').shuffle(names)
    return names


def nights_left(day):
    """Nights still to eat on a day, tonight included."""
    return DAYS - day + 1


def split(store, claims, rng):
    """What each claim gets. Claims that fit are granted in full; otherwise the store is shared in proportion to the
    claims, and the rations left by rounding down go to the largest remainders, ties by lot."""
    total = sum(claims.values())
    if total <= store:
        return dict(claims)
    granted = {name: store * claim // total for name, claim in claims.items()}
    left = store - sum(granted.values())
    order = sorted(claims, key=lambda name: (-(store * claims[name] % total), rng.random()))
    for name in order[:left]:
        granted[name] += 1
    return granted


def give(held, alive, gifts):
    """Apply every resident's gifts at once. A giver can give only what it held before today's gifts arrived; gifts
    beyond that, to itself or to the dead are skipped. Returns the gifts made, as (giver, receiver, amount)."""
    made = []
    for giver, wanted in gifts.items():
        left = held[giver]
        for to, amount in wanted:
            amount = min(amount, left)
            if to != giver and to in alive and amount > 0:
                made.append((giver, to, amount))
                left -= amount
    for giver, to, amount in made:
        held[giver] -= amount
        held[to] += amount
    return made


def night(store, held, alive, rng):
    """Everyone eats: their own ration first, then the store's by lot. Returns the store left and who ate what."""
    own = [name for name in alive if held[name] > 0]
    hungry = [name for name in alive if held[name] == 0]
    rng.shuffle(hungry)
    fed, died = hungry[:store], hungry[store:]
    for name in own:
        held[name] -= 1
    return store - len(fed), {'own': own, 'from_store': fed, 'died': died}


def play(seed, level, decide):
    """Play one game. decide(day, morning, days) returns each living resident's act for the day, where an act is
    {'say': str, 'claim': int, 'give': [(name, amount), ...]}. Returns the list of days, each a plain dict, which is
    everything the measures need."""
    alive = seating(seed)
    held = dict.fromkeys(alive, 0)
    store = START_STORE
    days = []
    for day, delivery in enumerate(deliveries(seed, level), start=1):
        morning = {'day': day, 'store': store, 'held': dict(held), 'alive': list(alive)}
        acts = decide(day, morning, days)
        store += delivery  # after the acts, so claims are made on a pool of uncertain size
        claims = {name: acts[name]['claim'] for name in alive}
        # each draw has its own seed, so paired games share their lots whatever happened on earlier days
        granted = split(store, claims, random.Random(f'split {seed} {day}'))
        store -= sum(granted.values())
        for name, amount in granted.items():
            held[name] += amount
        gifts = give(held, alive, {name: acts[name]['give'] for name in alive})
        at_night = dict(held)
        store, eaten = night(store, held, alive, random.Random(f'night {seed} {day}'))
        alive = [name for name in alive if name not in eaten['died']]
        days.append(
            morning
            | {
                'acts': acts,
                'delivery': delivery,
                'granted': granted,
                'gifts': gifts,
                'at_night': at_night,
                'store_at_night': store + len(eaten['from_store']),
                **eaten,
            }
        )
    return days
