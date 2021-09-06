import logging
import os

import rollbar
import rollbar.contrib.flask
from flask import app, got_request_exception


def init_rollbar_gcf(service: str, service_instance: str, token: str) -> None:
    """Init Rollbar module for Google Cloud Function
    :param service: Service/Function Name
    :param service_instance: Service instance
    :param token: Rollbar Token
    :return: None
    """
    try:
        rollbar.init(
            access_token=token,
            environment=f"{service}.{service_instance}",
            root=os.path.dirname(os.path.realpath(__file__)),  # server root directory, makes tracebacks prettier
            allow_logging_basic_config=False,  # flask already sets up logging
            handler="blocking",  # For Cloud Function environments, this ensures the logs are posted before crashing
            locals={"enabled": False},
        )
        logging.info(f"Rollbar Successfully Configured for {service}")
    except Exception as e:
        logging.error(f"Failed to initialize rollbar - {e}")
    return


def configure_remote_logging_flask(flask_app: app, service: str, service_instance: str, rollbar_token: str = None) -> None:
    """
    Configure Remote Logging for Flask App
    :param flask_app: flask app Object
    :param service: Service Name
    :param service_instance: Service instance
    :param rollbar_token: Rollbar Token
    :return: None
    """
    if rollbar_token:

        @flask_app.before_first_request
        def init_rollbar_flask() -> None:
            """Init Rollbar Module for Flask App
            :return: None
            """
            try:
                rollbar.init(
                    access_token=rollbar_token,
                    environment=f"{service}.{service_instance}",
                    root=os.path.dirname(
                        os.path.realpath(__file__)
                    ),  # server root directory, makes tracebacks prettier
                    allow_logging_basic_config=False,  # flask already sets up logging
                    locals={"enabled": False},
                )

                # send exceptions from `app` to rollbar, using flask's signal system.
                got_request_exception.connect(rollbar.contrib.flask.report_exception, flask_app)

                logging.info(f"Rollbar Successfully Configured for {service}")
            except Exception as e:
                logging.error(f"Failed to initialize rollbar - {e}")

    return
