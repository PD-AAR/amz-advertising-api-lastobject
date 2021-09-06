import logging
from functools import wraps
from typing import List

import rollbar
from flask import abort, request
from google.auth.transport import requests
from google.oauth2 import id_token


def serialize_exception(e: Exception, custom_error_message="", level="error") -> dict:

    """
    Simple resource for taking a caught exception and converting to JSON safe representation while also posting to rollbar and logging eror message
    """

    error_msg = custom_error_message or str(e)
    logging.error(error_msg)
    rollbar.report_message(error_msg, level)

    return {"error_type": type(e).__name__, "error_message": error_msg}


def cloud_task_restricted(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # this field is required should throw an error if not present
        queue = request.headers.get("X-AppEngine-QueueName") or request.headers.get("X-CloudTasks-QueueName")
        if queue is None:
            return abort(400)
        return func(*args, **kwargs)

    return wrapper


def cron_task_restricted(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # this field is required should throw an error if not present
        queue = request.headers.get("X-Appengine-Cron")
        if queue != "true":
            return abort(400)
        return func(*args, **kwargs)

    return wrapper


def cloud_scheduler_restricted(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # this field is required should throw an error if not present
        queue = request.headers.get("X-CloudScheduler")
        if queue is None:
            return abort(400)
        return func(*args, **kwargs)

    return wrapper


def invoker_restricted(authorized_domains: List[str] = [], authorized_accounts: List[str] = []):
    """
    Validate Invoker using Google Identity Token:
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # this field is required should throw an error if not present
            bearer_string = request.headers.get("Authorization")

            if bearer_string is None or (not bearer_string.lower().startswith("bearer ")):
                logging.warning("Bearer Header missing or malformed")
                return abort(400, "Bearer Header missing or malformed")

            token = bearer_string.replace("Bearer ", "").replace("bearer ", "")
            idinfo = id_token.verify_oauth2_token(token, requests.Request())

            if idinfo["iss"] not in [
                "accounts.google.com",
                "https://accounts.google.com",
            ]:
                logging.warning(f"Wrong Issuer: {idinfo['iss']}")
                return abort(400, f"Wrong Issuer: {idinfo['iss']}")
            email = idinfo.get("email")
            if email is None:
                logging.warning("email not found in JWT")
                return abort(400, "email not found in JWT")
            if (email.split("@")[1] in authorized_domains) or (email in authorized_accounts):
                logging.info("User email: {}".format(email))
                return func(*args, **kwargs, email=email)
            logging.warning(f"Attempted Unauthorized Access: {email}")
            return abort(400, f"Attempted Unauthorized Access: {email}")

        return wrapper

    return decorator
