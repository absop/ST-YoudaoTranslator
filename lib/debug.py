import json
import sublime


class Debug:
    _debug = False

    _header = __package__.split('.')[0]

    @classmethod
    def print(cls, *args):
        if cls._debug:
            print(cls._header + ':', *args)

    @classmethod
    def pprint(cls, obj):
        if cls._debug:
            print(cls._header + ':')
            print(json.dumps(obj,
                indent=4, sort_keys=True, ensure_ascii=False))

    @classmethod
    def set_debug(cls, debug):
        cls._debug = debug
        state = ['closing', 'opening'][debug]
        print(cls._header + ': debug is ' + state)

    def error(errmsg):
        sublime.error_message(errmsg)
