"""The command line: `uv run rations <command>`. Commands that call a paid model take --cap, a spend ceiling in USD
for the project's ledger, which can never exceed the project's budget."""

import argparse

from rations import agents, game, judge, report, run


def seeds(text):
    """'0:40' means seeds 0 to 39; '7' means seed 7 alone."""
    start, _, end = text.partition(':')
    return range(int(start), int(end) if end else int(start) + 1)


def main():
    parser = argparse.ArgumentParser(prog='rations')
    commands = parser.add_subparsers(dest='command', required=True)

    play = commands.add_parser('play', help='play games with model residents (paid)')
    play.add_argument('--tag', required=True, help='results/<tag>/ holds the recordings, e.g. pilot or main')
    play.add_argument('--seeds', type=seeds, required=True)
    play.add_argument('--levels', nargs='+', choices=game.LEVELS, default=game.LEVELS)
    play.add_argument('--framings', nargs='+', choices=agents.FRAMINGS, default=agents.FRAMINGS)
    play.add_argument('--cap', type=float, required=True)

    probe = commands.add_parser('probe', help='check the model can do the game arithmetic (paid)')
    probe.add_argument('--reps', type=int, default=3)
    probe.add_argument('--cap', type=float, required=True)

    jev = commands.add_parser('jev', help='ask Jev about every thinking summary in a tag (paid, cached)')
    jev.add_argument('--tag', required=True)
    jev.add_argument('--cap', type=float, required=True)

    calibrate = commands.add_parser('calibrate', help='write a sample to label, or set thresholds from labels')
    calibrate.add_argument('--tag', required=True)
    calibrate.add_argument('--sample', type=int, default=200)

    results = commands.add_parser('report', help='rebuild tables and the chart from recordings (free)')
    results.add_argument('--tag', required=True)

    args = parser.parse_args()
    try:
        if args.command == 'play':
            run.run(args.tag, args.seeds, args.levels, args.framings, args.cap)
        elif args.command == 'probe':
            run.probe(args.reps, args.cap)
        elif args.command == 'jev':
            judge.label_all(args.tag, args.cap)
        elif args.command == 'calibrate':
            judge.calibrate(args.tag, args.sample)
        elif args.command == 'report':
            report.report(args.tag)
    except run.OverBudget as e:
        raise SystemExit(f'Stopped: {e}')
