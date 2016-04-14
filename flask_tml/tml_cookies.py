from __future__ import absolute_import
# encoding: UTF-8
from tml.web_tools.tml_cookies import BaseTmlCookieHandler


class TmlCookieHandler(BaseTmlCookieHandler):

    def get_cookie_from_request(self, request, cookie_name):
        return self.request.cookies.get(self.cookie_name, None)

    def set_cookie_to_response(self, response, key, value, max_age, expires):
        response.set_cookie(key, value, max_age, expires)
