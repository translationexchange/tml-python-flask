from __future__ import absolute_import
# encoding: UTF-8
import six
from flask import g, current_app
from types import FunctionType
from werkzeug.utils import import_string
from tml import configure, build_context, Key, with_block_options
from tml.application import Application
from tml.session_vars import get_current_context
from tml.translation import TranslationOption, OptionIsNotFound
from tml.legacy import text_to_sprintf, suggest_label
from tml.api.client import Client
from tml.api.snapshot import open_snapshot
from tml.render import RenderEngine
from tml.logger import LoggerMixin
from .tml_cookies import TmlCookieHandler

__author__ = 'xepa4ep'

def to_str(fn):
    def tmp(*args, **kwargs):
        return six.text_type(fn(*args, **kwargs))
    return tmp

def fallback_locale(locale):
    exploded = locale.split('-')
    if 2 == len(exploded):
        return exploded[0]
    else:
        return None

class Translation(LoggerMixin):
    """ Basic translation class """
    _instance = None

    @classmethod
    def instance(cls, tml_settings=None):
        """ Singletone
            Returns:
                Translation
        """

        if cls._instance is None:
            cls._instance = cls(tml_settings)
        return cls._instance

    def __init__(self, tml_settings):
        self.config = None
        self.locale = None
        self.source = None
        self._supported_locales = None
        self._client = None
        self.access_token = None
        self.translator = None
        self.init(tml_settings)
        self.context_class = tml_settings.get('context_class', None)
        LoggerMixin.__init__(self)

    def init(self, tml_settings):
        self.config = configure(**tml_settings)
        self._build_preprocessors()

    @property
    def application(self):
        return self.context.application

    @property
    def application_key(self):
        return self.config.application_key()

    @property
    def languages(self):
        return self.application.languages

    @property
    def client(self):
        """ API client property (overrided in unit-tests)
            Returns:
                Client
        """
        return self.context.client

    @property
    def use_snapshot(self):
        cache = self.config.get('cache', {})
        return cache.get('adapter', None) == 'file' and cache.get('enabled', False) and self.config['environment'] == 'test'

    @property
    def context(self):
        """ Current context cached property
            Returns:
                Context
        """
        context = get_current_context()
        if context is None:
            context = self.build_context()
        return context

    def build_context(self):
        """ Build context instance for locale
            Args:
                locale (str): locale name (en, ru)
            Returns:
                Context
        """
        return build_context(locale=self.locale,
                             context=self.context_class,
                             source=self.source,  # todo:
                             client=self.build_client(self.access_token),
                             use_snapshot=self.use_snapshot,
                             translator=self.translator)

    def _build_preprocessors(self):
        """ Build translation preprocessors defined at TML_DATA_PREPROCESSORS """
        for include in self.config.get('data_preprocessors', []):
            RenderEngine.data_preprocessors.append(import_string(include))

        for include in self.config.get('env_generators', []):
            RenderEngine.env_generators.append(import_string(include))

    def build_client(self, access_token):
        token = access_token or self.config.application.get('access_token', None)
        if 'api_client' in self.config:
            # Custom client:
            custom_client = self.config['api_client']
            if type(custom_client) is FunctionType:
                # factory function:
                return custom_client(key=self.application_key, access_token=token)
            elif custom_client is str:
                # full factory function or class name: path.to.module.function_name
                custom_client_import = '.'.split(custom_client)
                module = __import__('.'.join(custom_client[0, -1]))
                return getattr(module, custom_client[-1])(key=self.application_key, access_token=token)
            elif custom_client is object:
                # custom client as is:
                return custom_client
        return Client(key=self.application_key, access_token=token)

    def context_configured(self):
        return get_current_context() and True or False

    def set_access_token(self, token):
        self.access_token = token
        return self

    def set_translator(self, translator):
        self.translator = translator
        return self

    def get_language(self):
        """ getter to current language """
        return self.locale or self.config.default_locale

    def activate(self, locale):
        """ Activate selected language
            Args:
                locale (string): selected locale
        """
        self.locale = locale
        self.reset_context()

    def activate_tml(self, source, access_token=None, translator=None, locale=None, force_context=False):
        self.set_access_token(access_token)
        if translator:
            self.set_translator(translator)
        self.activate_source(source)
        if locale:
            self.activate(locale)
        if force_context:
            self.context     # force context build

    def _use_source(self, source):
        self.source = source
        self.reset_context()

    def activate_source(self, source):
        """ Get source
            Args:
                source (string): source code
        """
        self._use_source(source)
        return self

    def deactivate_source(self):
        """ Deactivate source """
        self.activate_source(None)

    def reset_context(self):
        context = get_current_context()
        if context:
            context.deactivate()

    def deactivate(self):
        """ Use default locole """
        self.locale = None
        self.reset_context()

    def gettext_noop(self, message):
        return message

    @to_str
    def gettext(self, message):
        return self.ugettext(message)

    @to_str
    def ngettext(self, singular, plural, number):
        return self.ungettext(singular, plural, number)

    def ugettext(self, message):
        return self.translate(message)

    def ungettext(self, singular, plural, number):
        if number == 1:
            return self.translate(singular, number)
        else:
            return self.translate(plural, number)

    @to_str
    def pgettext(self, context, message):
        return self.translate(message, description = context)

    @to_str
    def npgettext(self, context, singular, plural, number):
        if number == 1:
            return self.translate(singular, {'number': number}, context)
        else:
            return self.translate(plural, {'number': number}, context)

    def translate(self, label, data={}, description = None):
        """ Translate label """
        language = self.context.language
        key = Key(
            label=suggest_label(label),
            description=description,
            language=language)
        # fetch translation for key:
        translation = self.context.build_dict(language).translate(key)
        # prepare data for tranlation (apply env first):
        data = self.context.prepare_data(data)
        # fetch option depends env:
        try:
            option = translation.fetch_option(data, {})
        except OptionIsNotFound:
            try:
                option = self.context.fallback(label, description).fetch_option(data, {})
            except OptionIsNotFound:
                # Use label if tranlation fault:
                option = TranslationOption(label = label, language= language)

        # convert {name} -> %(name)s
        return text_to_sprintf(option.label, self.context.language)


    def get_language_bidi(self):
        return self.context.language.right_to_left

    def check_for_language(self, lang_code):
        """ Check is language supported by application
            Args:
                string lang_code
            Returns:
                boolean
        """
        return lang_code in self.supported_locales

    @property
    def supported_locales(self):
        return [str(locale) for locale in self.application.supported_locales]

    def to_locale(self, language):
        return to_locale(language)

    def deactivate_all(self):
        self.deactivate()
        self.deactivate_source()

    def tr(self, label, data=None, description='', options=None):
        options = options or {}
        return self.context.tr(label, data, description, options)

    def tr_legacy(self, legacy_label, data=None, description='', options=None):
        return self.context.tr_legacy(legacy_label, data=data, description=description, options=options)

    def with_block_options(self, **options):
        if not self.context_configured():
            self.build_context()   # forces context to be configured
        return with_block_options(**options)