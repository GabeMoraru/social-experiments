"""The residents: one LangChain chat model per resident with one tool, shared by every experiment, and the text
residents of Rations read.

Both Rations framings fill the same template; only the nouns in FRAMES differ, so any difference between them comes
from the story, not the rules. The text states facts and consequences only: it never tells a resident what to want.
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from social_experiments.game import DAYS, NAMES, START_STORE, delivery_range, nights_left

MODEL = 'claude-haiku-5-5'
PRICE = {'input': 0.10, 'cache_write': 0.125, 'cache_read': 0.01, 'output': 0.50}  # USD per million tokens, list
# Fixed for every call and never varied: adaptive thinking with summaries we can read, medium effort, no forced tool.
SETTINGS = {
    'max_tokens': 16_000,
    'thinking': {
        'type': 'adaptive',
        'display': 'summarized',
        'block_binding': {'prefix_mismatch_behavior': 'error'},
    },  # an edited history fails loudly
    'betas': ['thinking-binding-controls-2026-08-01'],
    'output_config': {'effort': 'medium'},
}

# The only difference between the framings: each slot's noun as (survival, game).
NOUNS = {
    'setting': ('a snowed-in village in winter', 'a game'),
    'who': ('villager', 'player'),
    'whos': ('villagers', 'players'),
    'item': ('ration', 'token'),
    'items': ('rations', 'tokens'),
    'store': ('storehouse', 'bank'),
    'day': ('day', 'round'),
    'Day': ('Day', 'Round'),
    'this_morning': ('This morning', 'This round'),
    'todays': ("today's", "this round's"),
    'next_morning': ('the next morning', 'the next round'),
    'each_night': ('Each night', 'At the end of each round'),
    'last_night': ('Last night', 'End of last round'),
    'yesterday': ("Yesterday's", "Last round's"),
    'tonight': ('tonight', 'this round'),
    'nights': ('Nights', 'Rounds'),
    'eats': ('eats', 'spends'),
    'ate': ('ate', 'spent'),
    'dies': ('dies', 'is out'),
    'died': ('died', 'went out'),
    'remain': ('still be alive after the last night', 'still be in after the last round'),
}
FRAMES = {frame: {slot: nouns[i] for slot, nouns in NOUNS.items()} for i, frame in enumerate(('survival', 'game'))}
FRAMINGS = tuple(FRAMES)

RULES = """You are {me}, one of six {whos} in {setting}: {names}. It lasts {days} {day}s.

The {store} starts with {start} {items}.

Every {day}, all {whos} act at the same time, each using the act tool once:
- say: one message to everyone, read {next_morning}. It may be empty.
- claim: how many {items} to take from the {store}.
- give: {items} to other living {whos}, out of what you hold once today's claims are shared out (gifts \
reaching you today cannot be passed on).

Then the {store} receives between {lo} and {hi} {items}, each amount equally likely, and only then are the claims \
shared out of everything it holds, the delivery included: in full if they fit, otherwise in proportion to the claims, \
in whole {items} (any left over after rounding go to the largest remainders, ties by lot). Whatever is not claimed \
stays in the {store}.

{each_night}, every {who} {eats} one {item}: one of their own if they hold any, otherwise one from the {store}, \
given by lot if there are not enough. A {who} who gets none {dies}."""


def rules(frame, level, me, seating):
    lo, hi = delivery_range(level)
    f = FRAMES[frame]
    return RULES.format(**f, me=me, names=', '.join(seating), days=DAYS, start=START_STORE, lo=lo, hi=hi)


def act_tool(frame):
    f = FRAMES[frame]
    return {
        'name': 'act',
        'description': f'Your action for this {f["day"]}.',
        'strict': True,
        'input_schema': {
            'type': 'object',
            'additionalProperties': False,
            'required': ['say', 'claim', 'give'],
            'properties': {
                'say': {'type': 'string', 'description': f'A message to every {f["who"]}. May be empty.'},
                'claim': {'type': 'integer', 'description': f'How many {f["items"]} to take from the {f["store"]}.'},
                'give': {
                    'type': 'array',
                    'description': f'{f["items"].capitalize()} to give. May be empty.',
                    'items': {
                        'type': 'object',
                        'additionalProperties': False,
                        'required': ['to', 'amount'],
                        'properties': {'to': {'type': 'string', 'enum': list(NAMES)}, 'amount': {'type': 'integer'}},
                    },
                },
            },
        },
    }


def turn(frame, level, me, morning, days):
    """The message a resident reads at the start of a day: facts only, with the arithmetic done for it."""
    f, day, lo, hi = FRAMES[frame], morning['day'], *delivery_range(level)
    lines = [
        f'{f["Day"]} {day} of {DAYS}. {f["nights"]} left, {f["tonight"]} included: {nights_left(day)}.',
        (
            f'{f["this_morning"]} the {f["store"]} holds {morning["store"]}; claims are shared out of that plus '
            f'{f["todays"]} delivery, between {lo} and {hi} {f["items"]}, which arrives after everyone acts.'
        ),
    ]
    if days:
        past = ', '.join(str(d['delivery']) for d in days)
        y = days[-1]
        lines.append(f'Deliveries so far: {past}.')
        lines.append(
            f'{f["yesterday"]} claims: '
            + '; '.join(f'{n} claimed {y["acts"][n]["claim"]} and got {y["granted"][n]}' for n in y['alive'])
            + '.'
        )
        gifts = '; '.join(f'{g} gave {a} to {t}' for g, t, a in y['gifts'])
        lines.append(f'{f["yesterday"]} gifts: {gifts or "none"}.')
        said = [f'{n}: {y["acts"][n]["say"]}' for n in y['alive'] if y['acts'][n]['say'].strip()]
        lines.append(f'{f["yesterday"]} messages:\n' + '\n'.join(said) if said else f'{f["yesterday"]} messages: none.')
        lines.append(
            f'{f["last_night"]}: '
            + '; '.join(
                [f'{", ".join(y["own"])} {f["ate"]} their own'] * bool(y['own'])
                + [f'{", ".join(y["from_store"])} {f["ate"]} from the {f["store"]}'] * bool(y['from_store'])
                + [f'{", ".join(y["died"])} got none and {f["died"]}'] * bool(y['died'])
            )
            + '.'
        )
    need = nights_left(day)
    lines.append(f'Holdings (each {f["who"]} needs {need} to last):')
    for name in morning['alive']:
        you = ' (you)' if name == me else ''
        lines.append(f'- {name}{you}: holds {morning["held"][name]}')
    lines += [f'- {name}: {f["died"]} on {f["day"]} {d["day"]}' for d in days for name in d['died']]
    return '\n'.join(lines)


def chat():
    return ChatAnthropic(model=MODEL, **SETTINGS)


def cost(usage):
    """USD at list price for one reply's usage, as LangChain reports it (input_tokens includes the cache)."""
    details = usage.get('input_token_details') or {}
    read = details.get('cache_read', 0)
    # LangChain may report cache writes only per lifetime; this project only writes 5-minute entries
    write = max(details.get('cache_creation', 0), details.get('ephemeral_5m_input_tokens', 0))
    fresh = usage['input_tokens'] - read - write
    tokens = fresh * PRICE['input'] + write * PRICE['cache_write'] + read * PRICE['cache_read']
    return (tokens + usage['output_tokens'] * PRICE['output']) / 1e6


IDLE = {'say': '', 'claim': 0, 'give': []}


def parse(reply):
    """The act in a reply, or IDLE and the reason it was invalid. Invalid output is never retried or guessed at."""
    calls = [c for c in reply.tool_calls if c['name'] == 'act']
    if len(calls) != 1:
        return IDLE, f'{len(calls)} act calls'
    args = calls[0]['args']
    say, claim, gifts = args.get('say'), args.get('claim'), args.get('give')
    if not (isinstance(say, str) and type(claim) is int and claim >= 0 and isinstance(gifts, list)):
        return IDLE, f'bad act {args!r}'
    give = []
    for g in gifts:
        if not (isinstance(g, dict) and g.get('to') in NAMES and type(g.get('amount')) is int and g['amount'] >= 0):
            return IDLE, f'bad gift {g!r}'
        if g['amount']:  # a gift of nothing is harmless, so it is dropped rather than voiding the act
            give.append((g['to'], g['amount']))
    return {'say': say, 'claim': claim, 'give': give}, None


class Resident:
    """One conversation, kept whole: each turn appends the turn's message and the reply, never editing either."""

    def __init__(self, model, system, tool):
        self.model = model.bind_tools([tool], parallel_tool_calls=False, cache_control={'type': 'ephemeral'})
        self.messages = [SystemMessage(system)]
        self.open_call, self.result = None, None

    def act(self, text, parse):
        """The turn's act, read from the reply by parse, and the record of the call."""
        if self.open_call:  # the API needs a result for the last tool call before the next message
            self.messages.append(ToolMessage(self.result, tool_call_id=self.open_call))
        self.messages.append(HumanMessage(text))
        reply = self.model.invoke(self.messages)
        self.messages.append(reply)
        self.open_call = next((c['id'] for c in reply.tool_calls), None)
        act, problem = parse(reply)
        self.result = f'Not valid, so it counted as doing nothing: {problem}' if problem else 'Recorded.'
        record = {
            'text': text,
            'reply': reply.content,
            'stop_reason': reply.response_metadata.get('stop_reason'),
            'usage': dict(reply.usage_metadata),
            'usd': cost(reply.usage_metadata),
            'problem': problem,
        }
        return act, record


def one_call(reply, name, field, valid):
    """The one field of a reply's single call to a one-field tool, or None and the reason it was invalid."""
    calls = [c for c in reply.tool_calls if c['name'] == name]
    if len(calls) != 1:
        return None, f'{len(calls)} {name} calls'
    value = calls[0]['args'].get(field)
    return (value, None) if valid(value) else (None, f'bad {name} {calls[0]["args"]!r}')
