from __future__ import absolute_import
# encoding: UTF-8
from tml.utils import cached_property
from tml.logger import LoggerMixin
from tml.translator import Translator
from tml.utils import cookie_name as get_cookie_name, decode_cookie, encode_cookie


class TmlCookieHandler(LoggerMixin):

    def __init__(self, request, application_key):
        self.request = request
        self.cookie_name = get_cookie_name(application_key)

    @cached_property
    def tml_cookie(self):
        cookie = self.request.cookies.get(self.cookie_name, None)
        if not cookie:
            cookie = {}
        else:
            try:
                cookie = decode_cookie(cookie)
            except Exception as e:
                self.debug("Failed to parse tml cookie: %s", e.message)
                self.exception(e)
                cookie = {}
        return cookie

    def update(self, response, **kwargs):
        for k, v in kwargs.iteritems():
            self.tml_cookie[k] = v
        self.refresh(response)

    def refresh(self, response):
        response.set_cookie(self.cookie_name, encode_cookie(self.tml_cookie))

    @cached_property
    def tml_translator(self):
        translator_data = self.get_cookie('translator')
        return translator_data and Translator(**translator_data) or None

    @cached_property
    def tml_locale(self):
        return self.get_cookie('locale')

    @cached_property
    def tml_access_token(self):
        return self.get_cookie('oauth.token')

    def get_cookie(self, compound_key, default=None):
        key_parts = compound_key.split('.')
        val = self.tml_cookie
        while key_parts and val:
            cur_key = key_parts.pop(0)
            val = val.get(cur_key, default)
        return val or default
