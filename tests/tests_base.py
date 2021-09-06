import flask
import unittest

import config
import main

# Testing docs from Google
# https://cloud.google.com/functions/docs/testing/test-http

# GCP Testing Example Repo
# https://github.com/GoogleCloudPlatform/python-docs-samples/tree/master/functions/helloworld


class TestMainHTTPAPI(unittest.TestCase):
    def setUp(self) -> None:
        # Create a fake "app" for generating test request contexts.
        self.test_app = flask.Flask(__name__)

    def test_get_function_up(self):
        with self.test_app.test_request_context("/", method="GET"):
            resp = main.main(flask.request)
            self.assertIn(
                "Service is up",
                resp.data.decode("utf-8"),
            )

    def test_post_hello_name(self):
        with self.test_app.test_request_context("/", method="POST", json={"name": "test"}):
            resp = main.main(flask.request)
            self.assertEqual(resp.data.decode("utf-8"), "Hello test!")

    def test_post_hello_world(self):
        with self.test_app.test_request_context("/", method="POST"):
            resp = main.main(flask.request)
            self.assertEqual(resp.data.decode("utf-8"), "Hello World!")


