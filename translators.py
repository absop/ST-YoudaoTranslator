import re
import json
import uuid
import time
import hashlib
import requests
import mdpopups
import dctxmenu

import sublime
import sublime_plugin

from .log import Loger


user_settings = 'Translators.sublime-settings'

def plugin_loaded():
    def load_user_settings():
        TranslatorsCommand.caption = settings.get('caption', 'Translators')
        TranslatorsCommand.auto_select = settings.get('auto_select', True)
        TranslatorsCommand.style = settings.get('style', 'popup')
        TranslatorsCommand.mdpopups_css = settings.get('mdpopups.css', '')
        TranslatorsCommand.separator = settings.get('separator', '')
        YoudaoTranslation.load_user_data(settings.get('youdao'))
        GoogleTranslation.load_user_data(settings.get('google'))
        Loger.debug = settings.get('debug', False)

    settings = sublime.load_settings(user_settings)
    settings.clear_on_change('caption')
    settings.add_on_change('caption', load_user_settings)

    load_user_settings()

    sublime.set_timeout(
        lambda: dctxmenu.register(__package__,
            TranslatorsCommand.make_menu),
        500
    )

def plugin_unloaded():
    dctxmenu.deregister(__package__)


class translation:
    region = None
    words = None
    result = None


class TranslatorsCommand(sublime_plugin.TextCommand):
    style = 'popup'
    caption = 'Translators'
    mdpopups_css = 'Packages/DynamicMenus/mdpopups.css'
    auto_select = True
    user_data = {}
    separator = ''
    command = None

    @classmethod
    def load_user_data(cls, user_data):
        cls.enabled = user_data.pop('enabled', True)
        cls.caption = user_data.pop('caption', cls.caption)
        cls.user_data = user_data

    @classmethod
    def make_menu(cls, view, event):
        if not cls.get_words(view, event):
            return None
        items = []
        words = translation.words
        for sc in cls.__subclasses__():
            if sc.enabled and sc.caption and sc.command:
                item = dctxmenu.item(sc.caption,
                    sc.command, { 'action':  'translate'})
                items.append(item)
        if len(items) == 0:
            return None
        elif len(items) == 1:
            return items[0]
        else:
            return dctxmenu.fold_items(cls.caption, items)

    @classmethod
    def get_words(cls, view, event=None):
        def get_words_at(pt):
            region = view.word(pt)
            word = view.substr(region).strip(cls.separator)
            if len(word) > 0:
                translation.region = region
                translation.words = word
                return True
            return False

        if view.has_non_empty_selection_region():
            selected = view.sel()[0]
            words = view.substr(selected)
            lines = [l.lstrip(cls.separator) for l in words.split('\n')]
            words = ' '.join([l for l in lines if l])
            if len(words) > 0:
                translation.region = selected
                translation.words = words
                return True
        if event is None:
            return get_words_at(view.sel()[0])
        if cls.auto_select:
            return get_words_at(view.window_to_text((event["x"], event["y"])))
        return False

    def run(self, edit, action='translate', from_keyboard=False):
        if action == 'translate':
            if from_keyboard:
                TranslatorsCommand.get_words(self.view)
            if translation.words is not None:
                Loger.threading(
                    lambda: self.translate(translation.words),
                    'translating...'
                )
                translation.words = None
            else:
                sublime.status_message('No words to translate')

        elif action == 'copy':
            sublime.set_clipboard(translation.result)
            sublime.status_message('Translation copied to clipboard')

        elif action == 'insert':
            self.view.insert(edit,
                translation.region.end(), '\n%s\n' % translation.result)

        elif action == 'replace':
            self.view.replace(edit, translation.region, translation.result)

        elif action == 'toggle debug':
            Loger.debug = not Loger.debug
            sublime.load_settings(user_settings).set('debug', Loger.debug)
            sublime.save_settings(user_settings)

    def show_popup(self, region, content):
        def on_navigate(href):
            self.handle_href(href)
            self.view.hide_popup()

        mdpopups.show_popup(
            view=self.view,
            css=sublime.load_resource(self.mdpopups_css),
            max_width=480,
            max_height=320,
            location=(region.a + region.b)//2,
            content=content,
            on_navigate=on_navigate,
            md=True)

    def show_phantom(self, region, content):
        def on_navigate(href):
            self.handle_href(href)
            self.view.erase_phantoms(__package__)

        mdpopups.add_phantom(
            view=self.view,
            css=sublime.load_resource(self.mdpopups_css),
            key=__package__,
            region=region,
            content=content,
            layout=sublime.LAYOUT_BELOW,
            on_navigate=on_navigate,
            md=True)

    def show_view(self, content):
        view = self.view.window().new_file(
            flags=sublime.TRANSIENT,
            syntax="Packages/JavaScript/JSON.sublime-syntax")

        view.set_scratch(True)
        view.set_name("Translation")
        view.run_command("append", {"characters": content})

    def handle_href(self, href):
        self.view.run_command(self.name(), {"action": href})

    def display(self, words, res_data):
        pops = {
            "popup": self.show_popup,
            "phantom": self.show_phantom,
        }

        if self.style in pops:
            show = pops[self.style]
            show(translation.region, self.gen_markdown_text(words, res_data))

        elif self.style == "view":
            self.show_view(sublime.encode_value(res_data, pretty=True))

    def translate(self, words):
        pass

    def gen_markdown_text(self, words, res_data):
        return ""


TRANSLATOR_TEMPLATE = """
---
allow_code_wrap: true
---
!!! {}
"""

COPY_INSERT_REPLACE = """
<span class="copy"><a href=copy>Copy</a></span>&nbsp;&nbsp;&nbsp;&nbsp;<span class="insert"><a href=insert>Insert</a></span>&nbsp;&nbsp;&nbsp;&nbsp;<span class="replace"><a href=replace>Replace</a></span>
"""


class YoudaoTranslation(TranslatorsCommand):
    caption = 'Youdao Translation'
    command = 'youdao_translation'
    user_data = {}

    def translate(self, words):
        def truncate(q):
            size = len(q)
            return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]

        def encrypt(signStr):
            hash_algorithm = hashlib.sha256()
            hash_algorithm.update(signStr.encode('utf-8'))
            return hash_algorithm.hexdigest()

        user_data = YoudaoTranslation.user_data
        apiurl = user_data.get('api_url', '')
        appKey = user_data.get('app_id', '')
        secret = user_data.get('app_key', '')
        if (apiurl and appKey and secret):
            curtime = str(int(time.time()))
            salt = str(uuid.uuid1())
            sign = encrypt(appKey + truncate(words) + salt + curtime + secret)
            data = {
                'q': words,
                'from': user_data['from'],
                'to': user_data['to'],
                'appKey': appKey,
                'salt': salt,
                'sign': sign,
                'signType': 'v3',
                'curtime': curtime
            }

        else:
            data = { 'q': words }
            apiurl = 'http://fanyi.youdao.com/openapi.do?keyfrom=divinites&key=1583185521&type=data&doctype=json&version=1.1'

        try:
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            Loger.print('youdao translation: begin request')
            Loger.pprint(data)
            Loger.done_msg = 'Failed!'
            response = requests.post(
                apiurl, data=data, headers=headers, timeout=(1, 5))
            res_data = json.loads(response.content.decode('utf-8'))
            Loger.done_msg = 'Succeed.'
            Loger.print('youdao translation: succeed request')
            Loger.pprint(res_data)
        except requests.exceptions.ConnectionError:
            Loger.error(u'连接失败，请检查你的网络状态')
        except requests.exceptions.ConnectTimeout:
            Loger.error(u'连接超时，请检查你的网络状态')
        except Exception:
            Loger.error(u'数据请求失败！')
        else:
            self.display(words, res_data)

    # TODO: Use jieba to extract words, and then
    # combine those words as a sentence in proper
    # length, with considering the width of char.
    def gen_markdown_text(self, words, res_data):
        line = '\n------------------------\n{}'
        body = TRANSLATOR_TEMPLATE.format('Youdao')
        footer = '<div class="footer">'

        body += '## 原文：\n'
        body += words + '\n'

        if 'basic' in res_data and res_data['basic']:
            body += '## 解释：\n'
            for explain in res_data['basic']['explains']:
                body += '- {}\n'.format(explain)

        if 'translation' in res_data:
            body += '## 翻译：\n'
            explains = []
            for explain in res_data['translation']:
                explains.append(explain)
                explain = '\n'.join([
                    explain[i:i+24]
                    for i in range(0, len(explain), 24)
                ])
                body += '- {}\n'.format(explain)
            translation.result = '\n'.join(explains)
            body += COPY_INSERT_REPLACE

        if 'web' in res_data:
            body += line.format('## 网络释义:\n')
            for explain in res_data['web']:
                explains = ','.join(explain['value'])
                body += "`{}`: {}\n".format(explain["key"], explains)
        footer += '<span class="hide"><a href=hide>×</a></span></div>'

        return body + line.format(footer)


class GoogleTranslation(TranslatorsCommand):
    caption = 'Google Translation'
    command = 'google_translation'

    def run(self, edit, action='translate', from_keyboard=False):
        raise NotImplementedError('Google Translation')
