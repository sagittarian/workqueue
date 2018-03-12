import re
import time
from unittest.mock import MagicMock

import requests

from queueworker.worker import Worker


class TestWorker(object):
    def test_worker_process_next_task(self, tempdir, monkeypatch):
        url = 'localhost/api'
        delay = 1
        logfile = tempdir / 'worker_log.txt'

        result_id = 'abc123'
        test_payload = 'test payload'
        result = dict(status='ok',
                      task=dict(payload=test_payload,
                                id=result_id))
        json_mock = MagicMock(return_value=result)
        result_mock = MagicMock(json=json_mock)
        get_mock = MagicMock(return_value=result_mock)
        post_mock = MagicMock()

        monkeypatch.setattr(requests, 'get', get_mock)
        monkeypatch.setattr(requests, 'post', post_mock)

        worker = Worker(url, delay, logfile)

        start = time.time()
        worker.process_next_task()
        assert time.time() - start >= delay

        get_mock.assert_called_with(url + '/next')
        json_mock.assert_called_with()
        post_mock.assert_called_with(url + '/complete',
                                     json=dict(id=result_id))

        logline_re = r'^\d+-\d+-\d+T\d+:\d+:\d+: {}$'.format(test_payload)
        assert re.search(logline_re, logfile.read_text().strip())
