from __future__ import absolute_import
# encoding: UTF-8
__author__ = 'xepa4ep'

import os
import re
from json import dumps
from flask import request
from tml.config import CONFIG
from . import translator
from .tml_cookies import TmlCookieHandler


pj = os.path.join
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Tml(object):

    app = None
    _default_locale = None
    _config = None


    def __init__(self, app=None, default_locale='en', configure_jinja=True):
        self._default_locale = default_locale
        self._configure_jinja = configure_jinja
        self.app = app
        self.__before_response = set()
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Set up this instance for use with *app*, if no app was passed to
        the constructor.
        """
        self.app = app
        app.tml_instance = self
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['tml'] = self

        app.config.setdefault('TML_DEFAULT_LOCALE', self._default_locale)
        self._config = app.config['TML']
        self._config['logger'] = {}
        self._config['logger']['path']= pj(BASE_DIR, 'logs', 'tml.log')

        self.locale_selector_func = None

        if self._configure_jinja:
            app.jinja_env.add_extension('jinja2.ext.i18n')
            app.jinja_env.add_extension('tml_jinja2.ext.TMLExtension')
            app.jinja_env.install_gettext_callables(
                lambda x: translator.Translation.instance().ugettext(x),
                lambda s, p, n: translator.Translation.instance().ngettext(s, p, n),
                newstyle=True
            )
            app.jinja_env.install_tr_callables(
                tr=translator.Translation.instance(tml_settings=self._config).tr)

        app.before_request(self.activate_tml)
        app.after_request(self.deactivate_tml)
        app.after_request(self.agent_inject)
        self._previous_locale = None

    def ignore_tml(self):
        return not request.endpoint or request.endpoint == 'static'

    def activate_tml(self):
        if self.ignore_tml():  # ignore initialization of sdk
            return
        source = '%s' % (request.url_rule.endpoint)
        self.translation = translator.Translation.instance(tml_settings=self._config)
        cookie_handler = TmlCookieHandler(request, self.translation.application_key)
        locale = self.translation.get_language_from_request(
            request, cookie_handler, self.app.config)
        if locale != self._previous_locale:   # force template cache invalidation
            if self.app.jinja_env.cache:
                self.app.jinja_env.cache.clear()
        self.translation.activate_tml(
            source=source,
            access_token=cookie_handler.tml_access_token,
            translator=cookie_handler.tml_translator,
            locale=locale,
            force_context=True)
        return None

    def deactivate_tml(self, response):
        if self.ignore_tml():  # ignore initialization of sdk
            return response
        while self.translation._before_response:
            fn = self.translation._before_response.pop()
            fn(response)
        self._previous_locale = self.translation.locale
        translator.Translation.instance().deactivate_all()
        self.request = None
        self.translation = None
        return response

    def agent_inject(self, response):
        if self.ignore_tml():  # ignore initialization of sdk
            return response

        agent_config = CONFIG.get('agent', {})
        if not agent_config['force_injection']:
            return response

        if agent_config['enabled'] and agent_config['force_injection']:
            data = response.data
            pattern = re.compile(b'</head>', re.IGNORECASE)
            agent_script = self.app.jinja_env.from_string("{% tml_inline 'middleware' %}").render()
            response.data = pattern.sub(bytes(agent_script) + b'</head>', response.data)
            response.headers['Content-Length'] = len(response.data)

            return response
