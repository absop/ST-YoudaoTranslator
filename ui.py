import sublime
import sublime_plugin

import mdpopups

from .lib import youdao, Debug
from .lib import StatusBarTask, StatusBarThread


class YoudaoTranslatorCommand(sublime_plugin.TextCommand):
    translation = ''

    def description(self):
        return self.caption

    def is_visible(self):
        return self.get_selection() is not None

    def run(self, edit, action='translate'):
        getattr(self, action, self.translate)(edit)

    def get_selection(self):
        view = self.view
        selections = view.sel()
        if selections:
            region = selections[0]
            if not region.empty():
                dedented_lines = []
                for line in view.substr(region).split('\n'):
                    dedented_line = line.lstrip()
                    if dedented_line:
                        dedented_lines.append(dedented_line)
                content = ' '.join(dedented_lines)
                return content or None
            if self.auto_select:
                region = view.word(region)
                word = view.substr(region).strip(self.word_separators)
                if len(word) > 0:
                    return word
        return None

    def copy(self, edit):
        sublime.set_clipboard(self.translation)
        n = len(self.translation)
        sublime.status_message('Copied {} characters'.format(n))

    def insert(self, edit):
        region = self.view.sel()[0]
        self.view.insert(edit, region.end(), self.translation)

    def replace(self, edit):
        regions = list(self.view.sel())
        region0 = regions[0]
        size0 = region0.size()
        str0 = self.view.substr(region0)
        def eq0(r):
            if r.size() == size0:
                return self.view.substr(r) == str0
        for i in range(1, len(regions)):
            if not eq0(regions[i]):
                self.view.replace(edit, region0, self.translation)
                return
        for r in reversed(regions):
            self.view.replace(edit, r, self.translation)

    def translate(self, edit):
        content = self.get_selection()
        if not content:
            sublime.status_message('No words to translate')
            return
        compose = lambda f, g, h: lambda x: f(g(h(x)))
        process = compose(
            self.display,
            lambda x: self.generate_markdown(content, x),
            lambda x: youdao.query_translation(settings, x)
        )
        task = StatusBarTask(
            lambda: process(content),
            'Query translation...',
            'Succeed'
        )
        StatusBarThread(task, self.view.window())

    def display(self, content):
        mdpopups.show_popup(
            view=self.view,
            css=sublime.load_resource(self.mdpopups_css),
            max_width=480,
            max_height=320,
            content=content,
            on_navigate=self.on_navigate,
            md=True)

    def on_navigate(self, href):
        self.view.run_command(self.name(), {'action': href})

    @classmethod
    def generate_markdown(cls, text, json_data):
        line = '\n------------------------\n'
        body = """
---
allow_code_wrap: true
---
!!! Youdao

## 原文：
{}
""".format(text)

        if 'basic' in json_data and json_data['basic']:
            body += '## 解释：\n'
            for explain in json_data['basic']['explains']:
                body += '- {}\n'.format(explain)

        if 'translation' in json_data:
            body += '## 翻译：\n'
            explains = []
            for explain in json_data['translation']:
                explains.append(explain)
                explain = '\n'.join([
                    explain[i:i+24]
                    for i in range(0, len(explain), 24)
                ])
                body += '- {}\n'.format(explain)

            cls.translation = '\n'.join(explains)
            sep = 6 * '&nbsp;'
            body += sep.join(
                ('<a href="{}">{}</a>'.format(action, action.title())
                 for action in ['copy', 'insert', 'replace']
                 ))

        if 'web' in json_data:
            body += line + '## 网络释义:\n'
            for explain in json_data['web']:
                explains = ', '.join(explain['value'])
                body += "`{}`: {}\n".format(explain["key"], explains)
        return body + line

    @classmethod
    def init(cls):
        cls.caption = settings.get('caption', '有道翻译')
        cls.auto_select = settings.get('auto_select', True)
        cls.word_separators = settings.get('word_separators', '')
        cls.mdpopups_css = settings.get('mdpopups.css', '')
        Debug.set_debug(settings.get('debug', False))


def reload_settings():
    global settings
    settings = sublime.load_settings('YoudaoTranslator.sublime-settings')
    settings.add_on_change('__youdao__', YoudaoTranslatorCommand.init)
    YoudaoTranslatorCommand.init()


def plugin_loaded():
    sublime.set_timeout_async(reload_settings)


def plugin_unloaded():
    settings.clear_on_change('__youdao__')
