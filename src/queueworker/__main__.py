import argparse
from pathlib import Path

from .worker import Worker


DEFAULT_URL = 'http://localhost:5000/api'
DEFAULT_DELAY = 5
DEFAULT_LOGFILE = Path('./worker_log.txt')


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--url', '-u',
        default=DEFAULT_URL,
        help='Base URL to connect to for getting tasks and '
             'reporting them complete '
             '(default {}).'.format(DEFAULT_URL))
    parser.add_argument(
        '--delay', '-d', default=DEFAULT_DELAY, type=float,
        help='Time in seconds to wait between tasks '
             '(default {}).'.format(DEFAULT_DELAY))
    parser.add_argument(
        '--logfile', '-f', default=DEFAULT_LOGFILE,
        type=Path,
        help='Logfile to write completed tasks to '
             '(default {}).'.format(DEFAULT_LOGFILE))
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    worker = Worker(**vars(args))
    worker.run()


if __name__ == '__main__':
    main()
