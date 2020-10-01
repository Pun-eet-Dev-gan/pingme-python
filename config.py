from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))


class ProdConfig(object):
    DEBUG = False
    JSON_AS_ASCII = False  # b/[jsonify encoding]
    SQLALCHEMY_DATABASE_URI = 'mysql://yongwoo:dldyddn1@127.0.0.1/pingme'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    FIREBASE_CREDENTIAL = \
        "/home/yongwoo/IdeaProjects/ground-truth/pingme/service_account.json"
    FIREBASE_APP = {
        'storageBucket': "pingme-280512.appspot.com",
        'databaseURL': 'https://pingme-280512.firebaseio.com/'
    }
    MONGODB_SETTINGS = {
        'host': 'mongodb://127.0.0.1:27017/pingme-prod'
    }


class TestConfig(object):
    DEBUG = True
    TESTING = True
    JSON_AS_ASCII = False  # b/[jsonify encoding]
    FIREBASE_CREDENTIAL = \
        "/home/yongwoo/IdeaProjects/ground-truth/pingme/service_account.json"
    FIREBASE_APP = {
        'storageBucket': "pingme-280512.appspot.com",
        'databaseURL': 'https://pingme-280512.firebaseio.com/'
    }
    MONGODB_SETTINGS = {
        'host': 'mongodb://127.0.0.1:27017/pingme-test'
    }
    DEBUG_TB_PANELS = (
        "flask_debugtoolbar.panels.versions.VersionDebugPanel",
        "flask_debugtoolbar.panels.timer.TimerDebugPanel",
        "flask_debugtoolbar.panels.headers.HeaderDebugPanel",
        "flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel",
        "flask_debugtoolbar.panels.template.TemplateDebugPanel",
        "flask_debugtoolbar.panels.logger.LoggingPanel",
        "flask_mongoengine.panels.MongoDebugPanel",
    )
    DEBUG_TB_INTERCEPT_REDIRECTS = False


class UnitTestConfig(object):
    DEBUG = True
    TESTING = True
    JSON_AS_ASCII = False  # b/[jsonify encoding]
    FIREBASE_CREDENTIAL = \
        "/home/yongwoo/IdeaProjects/ground-truth/pingme/service_account.json"
    FIREBASE_APP = {
        'storageBucket': "staging.pingme-280512.appspot.com",
        'databaseURL': 'https://pingme-280512.firebaseio.com/'
    }
    MONGODB_SETTINGS = {
        'host': 'mongodb://127.0.0.1:27017/'
    }
    DEBUG_TB_PANELS = (
        "flask_debugtoolbar.panels.versions.VersionDebugPanel",
        "flask_debugtoolbar.panels.timer.TimerDebugPanel",
        "flask_debugtoolbar.panels.headers.HeaderDebugPanel",
        "flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel",
        "flask_debugtoolbar.panels.template.TemplateDebugPanel",
        "flask_debugtoolbar.panels.logger.LoggingPanel",
        "flask_mongoengine.panels.MongoDebugPanel",
    )
    DEBUG_TB_INTERCEPT_REDIRECTS = False
