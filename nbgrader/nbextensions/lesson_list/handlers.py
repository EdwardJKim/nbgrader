"""Tornado handlers for nbgrader lesson list web service."""

import os
import json
import subprocess as sp
import sys

from tornado import web

from notebook.utils import url_path_join as ujoin
from notebook.base.handlers import IPythonHandler
from traitlets import Unicode
from traitlets.config import LoggingConfigurable

static = os.path.join(os.path.dirname(__file__), 'static')

class LessonList(LoggingConfigurable):

    lesson_dir = Unicode('', config=True, help='Directory where the nbgrader commands should be run, relative to NotebookApp.notebook_dir')
    def _lesson_dir_default(self):
        return self.parent.notebook_dir

    def list_released_lessons(self):
        p = sp.Popen([sys.executable, "-m", "nbgrader", "list", "--json"], stdout=sp.PIPE, stderr=sp.PIPE, cwd=self.lesson_dir)
        output, _ = p.communicate()
        retcode = p.poll()
        if retcode != 0:
            raise RuntimeError('nbgrader list exited with code {}'.format(retcode))
        lessons = json.loads(output.decode())
        for lesson in lessons:
            if lesson['status'] == 'fetched':
                if lesson['prepend']:
                    lesson['assignment_id'] = os.path.join(
                        lesson['prepend'], lesson['assignment_id']
                    )
                lesson['path'] = os.path.relpath(lesson['path'], self.lesson_dir)
                for notebook in lesson['notebooks']:
                    notebook['path'] = os.path.relpath(notebook['path'], self.lesson_dir)
        return sorted(lessons, key=lambda x: (x['course_id'], x['assignment_id']))

    def list_submitted_lessons(self):
        p = sp.Popen([sys.executable, "-m", "nbgrader", "list", "--json", "--cached"], stdout=sp.PIPE, stderr=sp.PIPE, cwd=self.lesson_dir)
        output, _ = p.communicate()
        retcode = p.poll()
        if retcode != 0:
            raise RuntimeError('nbgrader list exited with code {}'.format(retcode))
        lessons = json.loads(output.decode())
        return sorted(lessons, key=lambda x: x['timestamp'], reverse=True)

    def list_lessons(self):
        lessons = []
        lessons.extend(self.list_released_lessons())
        lessons.extend(self.list_submitted_lessons())
        return lessons

    def fetch_lesson(self, course_id, assignment_id):
        p = sp.Popen([
            "nbgrader", "fetch",
            "--course", course_id,
            assignment_id
        ], stdout=sp.PIPE, stderr=sp.STDOUT, cwd=self.lesson_dir)
        output, _ = p.communicate()
        retcode = p.poll()
        if retcode != 0:
            self.log.error(output)
            raise RuntimeError('nbgrader fetch exited with code {}'.format(retcode))

    def submit_lesson(self, course_id, assignment_id):
        p = sp.Popen([
            sys.executable, "-m", "nbgrader", "submit",
            "--course", course_id,
            assignment_id
        ], stdout=sp.PIPE, stderr=sp.STDOUT, cwd=self.lesson_dir)
        output, _ = p.communicate()
        retcode = p.poll()
        if retcode != 0:
            self.log.error(output)
            raise RuntimeError('nbgrader submit exited with code {}'.format(retcode))

    def validate_notebook(self, assignment_id, notebook_id):
        p = sp.Popen([
            sys.executable, "-m", "nbgrader", "validate", "--json",
            os.path.join(assignment_id, "{}.ipynb".format(notebook_id))
        ], stdout=sp.PIPE, stderr=sp.PIPE, cwd=self.lesson_dir)
        output, _ = p.communicate()
        retcode = p.poll()
        if retcode != 0:
            raise RuntimeError('nbgrader validate exited with code {}'.format(retcode))
        return output.decode()


class BaseLessonHandler(IPythonHandler):

    @property
    def manager(self):
        return self.settings['lesson_list_manager']


class LessonListHandler(BaseLessonHandler):

    @web.authenticated
    def get(self):
        self.finish(json.dumps(self.manager.list_lessons()))


class LessonActionHandler(BaseLessonHandler):

    @web.authenticated
    def post(self, action):
        assignment_id = self.get_argument('assignment_id')
        course_id = self.get_argument('course_id')

        if action == 'fetch':
            self.manager.fetch_lesson(course_id, assignment_id)
            self.finish(json.dumps(self.manager.list_lessons()))
        elif action == 'submit':
            self.manager.submit_lesson(course_id, assignment_id)
            self.finish(json.dumps(self.manager.list_lessons()))
        elif action == 'validate':
            output = self.manager.validate_notebook(assignment_id, self.get_argument('notebook_id'))
            self.finish(json.dumps(output))


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_lesson_action_regex = r"(?P<action>fetch|submit|validate)"

default_handlers = [
    (r"/lessons", LessonListHandler),
    (r"/lessons/%s" % _lesson_action_regex, LessonActionHandler),
]


def load_jupyter_server_extension(nbapp):
    """Load the nbserver"""
    webapp = nbapp.web_app
    webapp.settings['lesson_list_manager'] = LessonList(parent=nbapp)
    base_url = webapp.settings['base_url']
    webapp.add_handlers(".*$", [
        (ujoin(base_url, pat), handler)
        for pat, handler in default_handlers
    ])
