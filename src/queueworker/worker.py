import time

import requests


class Worker(object):
    timestamp_format = '%Y-%m-%dT%H:%M:%S'
    def __init__(self, url, delay, logfile):
        self.url = url
        self.delay = delay
        self.logfile = logfile
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
        result = requests.get(self.next_url).json()
        return result['task']

    def report_complete(self, id):
        requests.post(self.complete_url, json=dict(id=id))

    def process_next_task(self):
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
        try:
            while True:
                self.process_next_task()
        except KeyboardInterrupt:
            pass
