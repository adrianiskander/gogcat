from flask import Flask

from flask_apscheduler import APScheduler

from . import config
from .gogapi import GOGAPI


app = Flask(__name__)
sched = APScheduler()
gogapi = GOGAPI(config)


def create_app(config):
    """Create new application instance."""
    app.config.from_object(config)

    try:
        sched.init_app(app)
        sched.start()
    except: # Scheduler is already running
        pass

    # Passby circular imports
    from . import routes

    return app
