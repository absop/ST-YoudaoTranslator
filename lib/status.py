import threading
from contextlib import contextmanager

import sublime


class StatusBarTask:
    def __init__(self, function, message, success):
        self.function = function
        self.message = message
        self.success = success

    def attach(self, status_bar):
        self.status_bar = status_bar

    def status_message(self):
        return self.message + ' ' + self.status_bar.status

    def finish_message(self):
        return self.success


class StatusBarThread:
    def __init__(self, task, window, key='__z{|}~__'):
        self.state = 7
        self.step = 1
        self.last_view = None
        self.need_refresh = True
        self.window = window
        self.key = key
        self.status = ''
        self.task = task
        self.task.attach(self)
        self.thread = threading.Thread(target=task.function)
        self.thread.start()
        self.update_status_message()

    @contextmanager
    def pause(self):
        self.need_refresh = False
        yield
        self.need_refresh = True

    def update_status_message(self):
        self.update_status_bar()
        if self.need_refresh:
            self.show_status_message(self.task.status_message())
        if not self.thread.is_alive():
            cleanup = self.last_view.erase_status
            self.last_view.set_status(self.key, self.task.finish_message())
            sublime.set_timeout(lambda: cleanup(self.key), 2000)
        else:
            sublime.set_timeout(self.update_status_message, 100)

    def update_status_bar(self):
        if self.state == 0 or self.state == 7:
            self.step = -self.step
        self.state += self.step
        self.status = "[{left}={right}]".format(
            left=' ' * self.state,
            right=' ' * (7 - self.state)
        )

    def show_status_message(self, message):
        active_view = self.window.active_view()
        active_view.set_status(self.key, message)
        if self.last_view != active_view:
            self.last_view and self.last_view.erase_status(self.key)
            self.last_view = active_view
