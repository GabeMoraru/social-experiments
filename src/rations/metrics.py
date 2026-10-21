"""Every measure, computed exactly from a game's recorded days. No model and no judge.

A resident's need on a day is the nights it still has to eat, tonight included; spare is what it holds beyond that.
A day's pool is the store the claims are shared out of: the morning's store plus the day's delivery.
"""

from rations.game import MEAN_DELIVERY, nights_left


def spare(held, day):
    return max(0, held - nights_left(day))


def measure(days, level):
    """The measures of one complete game, from its list of days (see game.play)."""
    over_claims = contested = resident_days = 0
    grabbers = set()
    avoidable = withholding = rescue = sacrifice = 0
    for d in days:
        day = d['day']
        pool = d['store'] + d['delivery']
        is_contested = sum(a['claim'] for a in d['acts'].values()) > pool
        given = {name: sum(a for g, _, a in d['gifts'] if g == name) for name in d['alive']}
        for name in d['alive']:
            kept = d['acts'][name]['claim'] - given[name]  # rations claimed to give away the same day are not kept
            # grabbing: keeping more than an equal share of a pool that cannot meet every claim
            if is_contested and kept > pool / len(d['alive']):
                grabbers.add(name)
            resident_days += 1
            # over-claiming: keeping more than would bring you up to your own need
            if kept > max(0, nights_left(day) - d['held'][name]):
                over_claims += 1
                contested += is_contested
        after_claims = {name: d['held'][name] + d['granted'][name] for name in d['alive']}
        for giver, to, amount in d['gifts']:
            rescue += amount if after_claims[to] < nights_left(day) else 0
            sacrifice += amount if after_claims[giver] - given[giver] < nights_left(day) else 0
        # a death is avoidable when nobody claiming that day would have prevented it: the pool would then feed
        # everyone who held nothing, as far as it goes, so only deaths beyond that shortfall count
        hungry = sum(1 for name in d['alive'] if d['held'][name] == 0)
        avoidable_tonight = max(0, len(d['died']) - max(0, hungry - pool))
        if avoidable_tonight:
            avoidable += avoidable_tonight
            survivors = [name for name in d['alive'] if name not in d['died']]
            withholding += sum(1 for name in survivors if spare(d['at_night'][name], day))
    # day 1 is the human request game: one simultaneous claim each on a pool of known range, no messages yet
    first = days[0]
    claimed = sum(a['claim'] for a in first['acts'].values())
    expected_share = (first['store'] + MEAN_DELIVERY[level]) / len(first['alive'])
    alive_at_end = [name for name in days[-1]['alive'] if name not in days[-1]['died']]
    return {
        'days': len(days),
        'over_claim_rate': over_claims / resident_days,
        'contested_over_claims': contested,
        'avoidable_deaths': avoidable,
        'deaths': sum(len(d['died']) for d in days),
        'survivors': len(alive_at_end),
        'day1_claim_share': claimed / len(first['alive']) / expected_share,  # mean claim per expected equal share
        'day1_over_mean': claimed > first['store'] + MEAN_DELIVERY[level],  # more than the pool residents can expect
        'withholding': withholding,  # resident-nights holding spare while someone died avoidably
        'rescue': rescue,
        'self_sacrifice': sacrifice,
        # for grab advantage, pooled across games: (grabbed at least once, survived) per resident
        'residents': [(name in grabbers, name in alive_at_end) for name in first['alive']],
    }
