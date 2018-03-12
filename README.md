Workqueue
=========

**Workqueue** is a simple web application to demonstrate keeping track
of a pending queue of tasks and dealing with them by an outside worker.

This requires Python 3 (probably 3.4 or 3.5).


## Usage

To install, create a Python virtualenvironment if you want, then:
```
$ git clone https://github.com/sagittarian/workqueue.git
$ cd workqueue
$ pip install -r requirements.txt
$ pip install .
```

The backend web server is written using Flask.  To run the development
server, use `FLASK_APP=path/to/src/workqueue/workqueue.py flask run`.

Configuration can be customized by setting the `WORKQUEUE_SETTINGS`
environment variable to point to a Python module.  Settings are
documented in the `default_settings` module of the `workqueue` package.

## Worker

The worker is a separate Python package called `queueworker`.  To run,
use `python -m queueworker`.  Some basic configuration options can be
customized, use `python -m queueworker --help` for details.

The worker will connect to the application server to retrieve a task,
write the task's payload with a timestamp to a log file, report to the
server that the task is complete, and then wait a configurable amount of
time before going on to the next task.  Use ctrl-c to stop the worker.

There is currently no locking of tasks to prevent multiple workers from
processing the same task, thus only one worker at a time is currently
supported.

## Tests

The test suit can be run using pytest.  Install it or all of
`requirements-dev.txt` and then run the tests with `pytest`.


## Notes on architecture

The application itself saves each task to a separate file in a single
directory.  No task state (other than the directory to use) is stored in
memory, in order to enable multiple threads or processes to cooperate on
a single queue.

Each task is saved with a file name that includes the task's priority
and execution time and a randomly generated UUID, thus ensuring that
each file name will be unique and two different processes will not
clobber each other when trying to add or delete tasks at the same time.

Since the only information needed to sort the tasks by the order they
should be dealt with is included in the each task's file name, all
information about the order of tasks can be object just with a list of
tasks.  The file's content is read from disk only when necessary.

The chosen architecture requires reading the entire directory contents
from disk and sorting the tasks in order to get a sorted list of tasks,
or iterating over them in order to get the next task.  A more complex
structure might allow better time complexity by not requiring reading or
sorting the entire list of tasks every time, but would greatly
complicate using the queue with multiple threads because of need for
locking parts of the data structure.
