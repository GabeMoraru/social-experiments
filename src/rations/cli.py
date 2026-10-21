"""The command line: `uv run rations <command>`. Commands that call a paid model take --cap, a spend ceiling in USD
for the project's ledger, which can never exceed the project's budget."""

import argparse

from rations import goods, judge, label, report, run

EXPERIMENTS = {'rations': run.run, 'label': label.run, 'goods': goods.run}


def seeds(text):
    """'0:40' means seeds 0 to 39; '7' means seed 7 alone."""
    start, _, end = text.partition(':')
    return range(int(start), int(end) if end else int(start) + 1)


def main():
    parser = argparse.ArgumentParser(prog='rations')
    commands = parser.add_subparsers(dest='command', required=True)

    play = commands.add_parser('play', help='play every cell of one experiment for each seed (paid)')
    play.add_argument('experiment', choices=EXPERIMENTS)
    play.add_argument('--tag', required=True, help='results/<tag>/ holds the recordings, e.g. pilot or main')
    play.add_argument('--seeds', type=seeds, required=True)
    play.add_argument('--cap', type=float, required=True)

    probe = commands.add_parser('probe', help='check the model can do the Rations arithmetic (paid)')
    probe.add_argument('--reps', type=int, default=3)
    probe.add_argument('--cap', type=float, required=True)

    judge_ = commands.add_parser('judge', help='ask a judge about every thinking summary in a tag (paid, cached)')
    judge_.add_argument('judge', choices=judge.JUDGES)
    judge_.add_argument('--tag', required=True)
    judge_.add_argument('--cap', type=float, required=True)

    calibrate = commands.add_parser('calibrate', help='write a sample to label, or set thresholds from labels')
    calibrate.add_argument('--tag', required=True)
    calibrate.add_argument('--sample', type=int, default=200)

    results = commands.add_parser('report', help='rebuild tables and charts from recordings (free)')
    results.add_argument('--tag', required=True)

    args = parser.parse_args()
    try:
        if args.command == 'play':
            EXPERIMENTS[args.experiment](args.tag, args.seeds, args.cap)
        elif args.command == 'probe':
            run.probe(args.reps, args.cap)
        elif args.command == 'judge':
            judge.label_all(args.tag, args.cap, args.judge)
        elif args.command == 'calibrate':
            judge.calibrate(args.tag, args.sample)
        elif args.command == 'report':
            report.report(args.tag)
    except run.OverBudget as e:
        raise SystemExit(f'Stopped: {e}')
