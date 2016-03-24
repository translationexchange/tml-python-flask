from __future__ import absolute_import
# encoding: UTF-8
import re
from datetime import datetime, timedelta
from time import mktime
from tml.tools.viewing_user import reset_viewing_user, set_viewing_user
from tml.rules.contexts.gender import Gender

__author__ = 'xepa4ep'


accept_language_re = re.compile(
   r'^[a-z]{1,8}(?:-[a-z0-9]{1,8})*(?:@[a-z0-9]{1,20})?$',
   re.IGNORECASE)


def ts():
    return int(mktime(datetime.utcnow().timetuple()))


def get_preferred_languages(request):
    accept = request.headers.get('http-accept-language', '')
    for accept_lang, unused in parse_accept_lang_header(accept):
        if accept_lang == '*':
            break
        if not language_code_re.search(accept_lang):
            continue
        if lang_code is not None:
            return accept_lang


def parse_accept_lang_header(lang_string):
   """
   Parses the lang_string, which is the body of an HTTP Accept-Language
   header, and returns a list of (lang, q-value), ordered by 'q' values.

   Any format errors in lang_string results in an empty list being returned.
   """
   result = []
   pieces = accept_language_re.split(lang_string.lower())
   if pieces[-1]:
       return []
   for i in range(0, len(pieces) - 1, 3):
       first, lang, priority = pieces[i:i + 3]
       if first:
           return []
       if priority:
           try:
               priority = float(priority)
           except ValueError:
               return []
       if not priority:        # if priority is 0.0 at this point make it 1.0
           priority = 1.0
       result.append((lang, priority))
   result.sort(key=lambda k: k[1], reverse=True)
   return result
