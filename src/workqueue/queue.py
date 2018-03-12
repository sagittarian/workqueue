import calendar
import json
import time
from datetime import datetime
from functools import total_ordering
from pathlib import Path
from uuid import uuid4


@total_ordering
class QueueTask(object):
    """Base class to represent a task object."""
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
        """Return a human readable timestamp of tasks's exectime."""
        if not self.exectime:
            return 'NOW'
        return datetime.isoformat(datetime.fromtimestamp(self.exectime))

    def asdict(self):
        """Return a dict representation of the task."""
        return dict(
            payload=self.payload,
            priority=self.priority,
            exectime = self.exectime,
            id=self.id,
        )

    @property
    def filename(self):
        """Return the canonical name where this task should be saved."""
        timestamp = time.strftime(self.timestamp_format,
                                  time.gmtime(self.exectime))
        priority = self.priority_fmt.format(self.priority)
        name = self.sep.join((timestamp, priority, str(self.id)))
        return name + '.json'

    def save(self):
        """Save this task to disk."""
        serialized = json.dumps(self.asdict())
        path = self.datadir / self.filename
        path.write_text(serialized)

    def delete(self):
        """Delete this task from disk."""
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
        """Initialize a task from a path.

        The task's exectime, priority, and id are parsed from the given
        filename itself.  Additional information (i.e. the payload) will
        be read from disk lazily only as needed.

        Args:
            path: The path to the saved task (a pathlib.Path object).

        """
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
        """Lazily load and return the payload for this task."""
        if self._payload is None:
            path = self.datadir / self.filename
            data = json.loads(path.read_text())
            self._payload = data['payload']
        return self._payload

    @payload.setter
    def payload(self, payload):
        self._payload = payload


class Queue(object):
    """Class representing a complete queue of pending tasks.

    The queue object does not save any state internally other than the
    directory in which to store the pending tasks, and each task is
    saved in a separate file which includes a UUID as part of the
    filename to eliminate the possibility of a collision, thus it should
    be safe to use in multiple threads and processes (to the degree that
    the system's filesystem itself is thread and process safe).

    """
    def __init__(self, datadir):
        """Initialize the Queue.

        Args:
            datadir: the directory in which pending tasks are stored
        """
        self.datadir = Path(datadir)

    def items(self):
        """Return a list of pending tasks (in no particular order).

        This is read from disk on every call.

        """
        return [FileQueueTask(path) for path in self.datadir.iterdir()]

    def peek(self):
        """Return the next pending task, or None if the queue is empty."""
        result = None
        # iterating through the items is slightly faster than sorting
        # and returning the first item, and works without change if the
        # queue is empty
        for item in self.items():
            if result is None or item < result:
                result = item
        return result

    def add(self, **kwds):
        """Add a new task to the queue."""
        item = QueueTask(datadir=self.datadir, **kwds)
        item.save()

    def delete_by_id(self, id):
        """Delete the task with the given id."""
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
