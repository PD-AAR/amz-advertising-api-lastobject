import logging
from typing import Optional

from flask import has_request_context, request


class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.trace = get_request_id(request=request)
        else:
            record.trace = None
        return super().format(record)


def get_request_id(request: request) -> Optional[str]:
    app_engine_task_name = request.headers.get("X-AppEngine-TaskName")
    http_target_task_name = request.headers.get("X-CloudTasks-TaskName")
    cloud_trace_id = request.headers.get("X-Cloud-Trace-Context")
    return next(
        (item for item in [app_engine_task_name, http_target_task_name, cloud_trace_id] if item is not None),
        None,
    )


def set_up_logging():
    formatter = RequestFormatter("%(trace)s:%(levelname)s:%(module)s:%(message)s")
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
