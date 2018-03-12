import calendar
import json
import time
from datetime import datetime
from functools import total_ordering
from pathlib import Path
from uuid import uuid4


@total_ordering
class QueueTask(object):
    sep = '_'
    priority_fmt = '{:08}'
    timestamp_format = '%Y-%m-%dT%H:%M:%S'

    def __init__(self, payload, priority, datadir, exectime=0, id=None):
        """Represent an item to be dealt with in the queue.

        This class has a total ordering defined on it with an item
        preceding another item if it to be excuted first.

        Args:
            payload: a string indicating what the task is
            priority: tiebreaker for tasks with the same execution time,
                higher value means higher priority
            exectime: when to execute the task in unix time (the default
                of 0 means ASAP)
            id: the id of the item, which will be a randomly generated
                uuid if not given

        """
        self.payload = payload
        self.priority = priority
        self.exectime = exectime
        self.datadir = datadir
        if id is None:
            id = str(uuid4())
        self.id = id

    def pretty_exectime(self):
        if not self.exectime:
            return 'NOW'
        return datetime.isoformat(datetime.fromtimestamp(self.exectime))

    def asdict(self):
        return dict(
            payload=self.payload,
            priority=self.priority,
            exectime = self.exectime,
            id=self.id,
        )

    @property
    def filename(self):
        timestamp = time.strftime(self.timestamp_format,
                                  time.gmtime(self.exectime))
        priority = self.priority_fmt.format(self.priority)
        name = self.sep.join((timestamp, priority, str(self.id)))
        return name + '.json'

    @filename.setter
    def filename(self, name):
        self.__dict__[filename] = name

    def save(self):
        serialized = json.dumps(self.asdict())
        path = self.datadir / self.filename
        path.write_text(serialized)

    def delete(self):
        path = self.datadir / self.filename
        path.unlink()

    def __lt__(self, other):
        # Tasks are ordered first by execution time then by priority.
        # XXX Should we consider all tasks whose execution time has
        # already passed to be equal in execution time, even if they
        # weren't originally scheduled at the same time?
        return (self.priority > other.priority
                if self.exectime == other.exectime
                else self.exectime < other.exectime)

    def __eq__(self, other):
        return (self.exectime == other.exectime and
                self.priority == other.priority)

    def __str__(self):
        name = type(self).__name__
        args = ', '.join('{}={!r}'.format(key, value)
                         for (key, value) in self.__dict__.items())
        return '{name}({args})'.format(name=name, args=args)


class FileQueueTask(QueueTask):
    """Version of QueueTask that is loaded from disk.

    Since all the data needed to determine the relative order of which
    tasks to do when, any information which must be read from the file
    itself (i.e., the payload) is read lazily only when it is actually
    needed.

    """

    def __init__(self, path):
        self._filename = path.name
        datadir = path.parent
        stem = path.stem
        timestamp, priority, id = stem.split(self.sep, 2)
        exectime = calendar.timegm(time.strptime(timestamp,
                                                 self.timestamp_format))
        priority = int(priority)
        super().__init__(payload=None,
                         exectime=exectime, priority=priority, id=id,
                         datadir=datadir)

    @property
    def filename(self):
        return self._filename

    @property
    def payload(self):
        if self._payload is None:
            path = self.datadir / self.filename
            data = json.loads(path.read_text())
            self._payload = data['payload']
        return self._payload

    @payload.setter
    def payload(self, payload):
        self._payload = payload


class Queue(object):
    def __init__(self, datadir):
        self.datadir = Path(datadir)

    def items(self):
        return [FileQueueTask(path) for path in self.datadir.iterdir()]

    def peek(self):
        """
        Return the next item on the queue, or None if the queue is empty.
        """
        result = None
        # iterating through the items is slightly faster than sorting
        # and returning the first item, and works without change if the
        # queue is empty
        for item in self.items():
            if result is None or item < result:
                result = item
        return result

    def add(self, **kwds):
        item = QueueTask(datadir=self.datadir, **kwds)
        item.save()

    def delete_by_id(self, id):
        for item in self.items():
            if item.id == id:
                try:
                    item.delete()
                except IOError:
                    pass
                return
        # ignore if not found or we get an error, maybe another
        # thread/process deleted it in the meantime

    def __str__(self):
        name = type(self).__name__
        items = ', '.join(str(item) for item in self.items())
        return '<{name}: {items}>'.format(name=name, items=items)
