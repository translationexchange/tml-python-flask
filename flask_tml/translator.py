from __future__ import absolute_import
# encoding: UTF-8
from tml.web_tools.translator import BaseTranslation

author = 'xepa4ep'


class Translation(BaseTranslation):
    """ Basic translation class """

    def get_language_from_request(self, request, cookie_handler, config):
        locale = None
        locale = request.args.get('locale', None)
        if not locale:
            locale = cookie_handler.tml_locale
            if not locale:
                if self.config.locale.get('subdomain', None):
                    locale = request.host[:-len(config['SERVER_NAME'])].rstrip('.')
                else:
                    locale = self.get_preferred_languages(request)
        else:
            self._before_response.add(
                lambda response: cookie_handler.update(response, locale=locale))
        return locale

    def get_header_from_request(self, request, header):
        return request.headers.get('http-accept-language', '')
