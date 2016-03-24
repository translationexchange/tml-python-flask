# from django.test import SimpleTestCase

import pytest
import os
import tempfile
import six
from flask import Flask
from flask_tml import tml
from jinja2.environment import Template
from tml.strings import to_string


__author__ = 'xepa4ep'


class FakeUser(object):

    first_name = 'Tom'
    last_name = 'Anderson'
    gender = 'male'

    def __init__(self, **kwargs):
        for k, v in six.iteritems(kwargs):
            setattr(self, k, v)

    def __str__(self):
        return self.first_name + " " + self.last_name

def test_tml_init(dummy_app):
    tml_mod = tml.Tml(dummy_app)
    assert isinstance(dummy_app.tml_instance, tml.Tml), 'should be instance of tml.Tml'
    assert isinstance(tml_mod._config, dict), '`_config` attribute should be set'
    if tml_mod._configure_jinja:
        assert 'tml_jinja2.ext.TMLExtension' in dummy_app.jinja_env.extensions, 'extensions must be configured'
    assert hasattr(tml_mod, '_previous_locale'), '`_previous_locale` attribute should be set'

def test_tml_lifecycle(dummy_app):
    tml_mod = tml.Tml(dummy_app)
    pass

def test_tr_tag(get_template):
    assert to_string("hello") == get_template(to_string("hello")).render(), "Dummy test"
    users = {
        'michael': FakeUser(**{'gender': 'male', 'first_name': 'Michael', 'last_name': 'Berkovitch'}),
        'anna': FakeUser(**{'gender': 'female', 'first_name': 'Anna', 'last_name': 'Tusso'})
    }
    tmpl = to_string("{% tr user=users.michael %}Hello {user}{% endtr %}")
    assert to_string(get_template(tmpl).render(users=users)) == to_string('Hello Michael Berkovitch')

    tmpl = to_string("{% tr user=[users.michael, ':first_name'] %}Hello {user}{% endtr %}")
    assert to_string(get_template(tmpl).render(users=users)) == to_string('Hello Michael')

    tmpl = to_string("{% tr user=[users.michael, 'Michaell'] %}Hello {user}{% endtr %}")
    assert to_string(get_template(tmpl).render(users=users)) == to_string('Hello Michaell')

    tmpl = to_string("{% tr user=users.michael %}Hello {user.first_name}{% endtr %}")
    assert to_string(get_template(tmpl).render(users=users)) == to_string('Hello Michael')

    tmpl = to_string("{% tr user={'object': users.michael, 'attribute': 'first_name'} %}Hello {user}{% endtr %}")
    assert to_string(get_template(tmpl).render(users=users)) == to_string('Hello Michael')

    tmpl = to_string("{% tr user={'object': users.michael, 'property': 'last_name'} %}Hello {user}{% endtr %}")
    assert to_string(get_template(tmpl).render(users=users)) == to_string('Hello Berkovitch')

    tmpl = to_string("{% tr user={'object': users.michael, 'value': 'Michael'} %}Hello {user}{% endtr %}")
    assert to_string(get_template(tmpl).render(users=users)) == to_string('Hello Michael')

    # list tokens
    tmpl = to_string("{% tr users=[users.values(), ':first_name'] %}Hello {users}{% endtr %}")
    assert to_string(get_template(tmpl).render(users=users)) == to_string('Hello Michael and Anna')

    tmpl = to_string("{% tr users=[users.values(), '<b>{$0}</b>'] %}Hello { users}{% endtr %}")
    assert to_string(get_template(tmpl).render(users=users)) == to_string('Hello <b>Michael Berkovitch</b> and <b>Anna Tusso</b>')

    tmpl = to_string("{% tr users=[users.values(), ':first_name', {'joiner': 'or'}] %}Hello { users}{% endtr %}")
    assert to_string(get_template(tmpl).render(users=users)) == to_string('Hello Michael or Anna')

    # transform tokens
    tmpl = to_string("{% tr user=users.anna %}This is {user|he,she,it}{% endtr %}")
    assert to_string(get_template(tmpl).render(users=users)) == to_string('This is she')

    tmpl = to_string("{% tr user=users.michael %}This is {user|male: he, female: she, other: it}{% endtr %}")
    assert to_string(get_template(tmpl).render(users=users)) == to_string('This is he')