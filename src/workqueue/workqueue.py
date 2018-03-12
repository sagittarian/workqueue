import calendar
import os
import time
from pathlib import Path

from flask import Flask, request, render_template, url_for, redirect
from flask.json import jsonify

from .queue import Queue
from . import default_settings

app = Flask(__name__)
app.config.from_object(default_settings)
if os.environ.get('WORKQUEUE_SETTINGS'):
    app.config.from_envvar('WORKQUEUE_SETTINGS')

queue = Queue(app.config['QUEUEDIR'])
default_priority = app.config['DEFAULT_PRIORITY']


@app.route('/')
def main():
    """Main page showing the next task and a form to add a new task."""
    return render_template('index.html',
                           item=queue.peek(),
                           default_priority=default_priority)


@app.route('/list')
def itemlist():
    """Page showing a full list of all pending tasks.

    Also includes a form to add a new task.

    """
    return render_template('list.html',
                           items=sorted(queue.items()),
                           default_priority=default_priority)


@app.route('/new', methods=['POST'])
def new():
    payload = request.form['payload']

    try:
        priority = int(request.form['priority'])
    except (ValueError, KeyError):
        priority = default_priority

    formats = ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S')
    for fmt in formats:
        try:
            timestamp = time.strptime(request.form['exectime'], fmt)
        except ValueError:
            pass
        else:
            exectime = calendar.timegm(timestamp)
            break
    else:
        exectime = 0

    queue.add(payload=payload, priority=priority, exectime=exectime)
    return redirect(url_for('main'))


@app.route('/delete', methods=['POST'])
def delete():
    id = request.form['id']
    queue.delete_by_id(id)
    return redirect(url_for('itemlist'))


@app.route('/api/next')
def api_next():
    task = queue.peek()
    task_json = task and task.asdict()
    return jsonify(status='ok', task=task_json)


@app.route('/api/complete', methods=['POST'])
def api_complete():
    task = queue.delete_by_id(request.json['id'])
    return jsonify(status='ok')
