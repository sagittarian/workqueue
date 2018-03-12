import json
import random
import time

from workqueue.queue import QueueTask, FileQueueTask, Queue


class TestQueue:
    def test_task(self, tempdir):
        payload = 'test payload'
        priority = 100
        exectime = 1500000000
        timestamp = '2017-07-14T02:40:00'
        task_id =  '5741fd6f-4388-482b-a7e1-5fc1c164c83e'
        task = QueueTask(payload=payload, priority=priority,
                         exectime=exectime, id=task_id,
                         datadir=tempdir)

        filename = ('2017-07-14T02:40:00_00000100_'
                    '5741fd6f-4388-482b-a7e1-5fc1c164c83e.json')
        assert filename == task.filename, \
            'Expected filename {}, got {}'.format(filename,
                                                  task.filename)

        task.save()
        path = tempdir / filename
        assert path.exists(), \
            'Expected task path {} not found'.format(path)

        content = json.loads(path.read_text())
        keys = ('payload', 'priority', 'exectime', 'id')
        for key in keys:
            assert key in content, 'Key {!r} not found'.format(key)

        task.delete()
        assert not path.exists(), \
            'Task path still exists after task is deleted'

    def test_task_compare(self, tempdir):
        timestamp = time.time() + 1000000
        task1 = QueueTask(payload='',
                          priority=100, datadir=tempdir,
                          exectime=timestamp)
        task2 = QueueTask(payload='',
                          priority=150, datadir=tempdir,
                          exectime=timestamp-50)
        task3 = QueueTask(payload='',
                          priority=150, datadir=tempdir,
                          exectime=timestamp)
        assert task2 < task1
        assert task3 < task1
        assert task2 < task3

    def test_file_task(self, tempdir):
        task = QueueTask(payload='test', priority=500,
                         exectime=int(time.time()),
                         datadir=tempdir)
        path = tempdir / task.filename
        assert not path.exists()
        task.save()
        assert path.exists()

        loaded_task = FileQueueTask(path)
        assert loaded_task.payload == task.payload
        assert loaded_task.exectime == task.exectime
        assert loaded_task.priority == task.priority
        assert loaded_task.id == task.id

        loaded_task.delete()
        assert not path.exists()

    def run_queue_test(self, tempdir, task_kwds):
        queue = Queue(tempdir)

        shuffled = list(task_kwds)
        random.shuffle(shuffled)
        for kwds in shuffled:
            queue.add(**kwds)

        top = queue.peek()
        assert top.priority == task_kwds[-1]['priority']
        assert top.exectime == task_kwds[-1]['exectime']
        assert top.payload == task_kwds[-1]['payload']

        sorted_tasks = sorted(queue.items(), reverse=True)
        for (task, kwds) in zip(sorted_tasks, task_kwds):
            for (key, val) in kwds.items():
                assert getattr(task, key) == val

        randtask = random.choice(sorted_tasks)
        path = tempdir / randtask.filename
        assert path.exists()
        queue.delete_by_id(randtask.id)
        assert not path.exists()
        for task in queue.items():
            taskpath = tempdir / task.filename
            if task.id != randtask.id:
                assert taskpath.exists()

    def test_queue_priority(self, tempdir):
        timestamp = int(time.time() + 1000000)
        task_kwds = [dict(priority=100+i,
                          exectime=timestamp,
                          payload='test {}'.format(i))
                     for i in range(100)]
        self.run_queue_test(tempdir, task_kwds)

    def test_queue_exectime(self, tempdir):
        timestamp = int(time.time() + 1000000)
        task_kwds = [dict(priority=200-i,
                          exectime=timestamp-i,
                          payload='test {}'.format(i))
                     for i in range(100)]
        self.run_queue_test(tempdir, task_kwds)
