import time
from pathlib import Path

import requests


class Worker(object):
    """Simple worker to process tasks."""

    timestamp_format = '%Y-%m-%dT%H:%M:%S'

    def __init__(self, url, delay, logfile):
        """Initialize a new worker to process tasks.

        Args:
            url: base API url for retrieving and reporting on tasks
            delay: time in seconds to wait between tasks
            logfile: log file to write completed tasks to
        """
        self.url = url
        self.delay = delay
        self.logfile = Path(logfile)
        self.next_url = self.url + '/next'
        self.complete_url = self.url + '/complete'
        self.cur_task = None

    def current_timestamp(self):
        return time.strftime(self.timestamp_format, time.gmtime())

    def writeline(self, line):
        full_line = '{timestamp}: {line}\n'.format(
            timestamp=self.current_timestamp(), line=line)
        with self.logfile.open('a') as fp:
            fp.write(full_line)

    def get_task(self):
        result = requests.get(self.next_url)
        return result.json()['task']

    def report_complete(self, id):
        requests.post(self.complete_url, json=dict(id=id))

    def process_next_task(self):
        """Retrieve and process the next task and report its completion."""
        task = self.get_task()
        if task is not None:
            payload = task['payload']
            id = task['id']
            self.writeline(payload)
            self.report_complete(id)
            print('Completed task {} with payload {!r}'.format(id, payload))
        else:
            print('No current task')
        time.sleep(self.delay)

    def run(self):
        """Run in an infinite loop processing tasks."""
        try:
            while True:
                self.process_next_task()
        except KeyboardInterrupt:
            pass
        except requests.exceptions.ConnectionError:
            print('Cannot connect to server.')
