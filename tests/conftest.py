import pytest
from flask import Flask, render_template
from flask_tml import tml


@pytest.fixture(scope='module')
def app(request):
    app = Flask(__name__)
    app.config.from_pyfile('app.cfg')
    app.config['TESTING'] = True
    tml.Tml(app)

    def teardown():
        pass

    @app.route('/')
    def index():
        return "OK"

    @app.route('/template')
    def template():
        return render_template('base.html')

    request.addfinalizer(teardown)
    return app


@pytest.fixture
def dummy_app(request):
    app = Flask(__name__)
    app.config.from_pyfile('app.cfg')
    app.config['TESTING'] = True
    def teardown():
        pass

    request.addfinalizer(teardown)
    return app


@pytest.fixture
def get_template(app):

    def _get_template(template_string):
        return app.jinja_env.from_string(template_string)

    return _get_template
