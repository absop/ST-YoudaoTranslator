import os
import json
import threading

import sublime


class Loger:
    debug = False
    employer = __package__
    done_msg = ""

    def print(*args):
        if Loger.debug:
            print("%s:" % Loger.employer, *args)

    def pprint(obj, print_head=False):
        if Loger.debug:
            if print_head:
                print(Loger.employer + ':')
            print(json.dumps(obj,
                indent=4, sort_keys=True, ensure_ascii=False))

    def error(errmsg):
        sublime.error_message(errmsg)

    def relative_path(path):
        for folder in sublime.active_window().folders():
            if path.startswith(folder):
                return path[len(os.path.dirname(folder)):]
        return path

    def threading(function, ing_msg, done_msg="", on_done=None):
        def check(last_view, i, d):
            active_view = sublime.active_window().active_view()
            if last_view != active_view:
                last_view.erase_status(Loger.employer)

            if not thread.is_alive():
                cleanup = active_view.erase_status
                Loger.print(Loger.done_msg)
                active_view.set_status(Loger.employer, Loger.done_msg)
                sublime.set_timeout(lambda: cleanup(Loger.employer), 2000)
                if on_done is not None:
                    on_done()
                return

            dynamic = " [%s=%s]" % (' ' * i, ' ' * (7 - i))
            active_view.set_status(Loger.employer, ing_msg + dynamic)

            if i == 0 or i == 7:
                d = -d

            sublime.set_timeout(lambda: check(active_view, i + d, d), 100)

        Loger.done_msg = done_msg
        Loger.print("Start " + ing_msg)
        thread = threading.Thread(target=function)
        thread.start()
        check(sublime.active_window().active_view(), 0, -1)
