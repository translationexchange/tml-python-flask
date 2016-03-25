# encoding: UTF-8
from datetime import date, timedelta
from json import loads
from flask import Flask, request, render_template
from flask_tml import tml, translator
from tml.strings import to_string
from tml.translation import TranslationOption
from tml.decoration.parser import parse as decoration_parser
from .models import User


app = Flask(__name__)
app.config.from_pyfile('settings.cfg')
app.config.from_envvar('TML_DEMO_SETTINGS', silent=True)
tml.Tml(app)


@app.route('/')
def index():
    import pdb
    pdb.set_trace()
    return render_template('docs/index.html')


@app.route('/docs/')
def docs():
    users = {
        'michael': User(to_string("Michael"), User.MALE),
        'alex': User("Alex", User.MALE),
        'anna': User(to_string("Anna"), User.FEMALE),
        'jenny': User("Jenny", User.FEMALE),
        'peter': User(to_string("Petr"), User.MALE),
        'karen': User("Karen", User.FEMALE),
        'thomas': User("Thomas", User.MALE),
    }
    data = {
        'users': users,
        'user_list': users.values(),
        'ten': xrange(1, 10),
        'five': xrange(1, 5),
        'dates': [
            date.today(),
            date.today() - timedelta(days=1),
            date.today() + timedelta(days=1)],
        'current_date': date.today()
    }
    return render_template('docs/docs.html', users=data['users'], user_list=data['user_list'], ten=data['ten'], five=data['five'], dates=data['dates'], current_date=data['current_date'])


@app.route('/console/')
def console():
    return render_template('docs/console.html')


@app.route('/translate/', methods=['GET', 'POST'])
def translate():
    if not request.method.lower() == "post":
        return ""
    label = request.form.get('tml_label')
    data = loads(request.form.get('tml_tokens') or "{}")
    description = request.form.get('tml_context')
    locale = request.form.get('tml_locale')
    trans_value = fetch_translation(label, data, description, locale)
    return trans_value

def fetch_translation(label, data, description, locale):
    translator.Translation.instance().activate(locale)
    language = translator.Translation.instance().context.language
    option = translator.TranslationOption(label, language)
    return decoration_parser(option.execute(data, options={})).render(data)


