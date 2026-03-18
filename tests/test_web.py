import os

import unittest
from unittest.mock import patch, Mock

from webtest import TestApp
from presentation_validator.web import create_app
from pathlib import Path
import json

def mockRequests(local_manifest, headers=None):
    if headers is None:
        headers = {
            "content-type": "application/json",
            "access-control-allow-origin": "*",
            "Content-Encoding": "gzip",
            "Vary": "Accept-Encoding",
        }

    # Load JSON from file
    path = Path(local_manifest)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    mock_response = Mock()
    mock_response.headers = headers
    mock_response.json.return_value = data
    mock_response.raise_for_status.return_value = None

    return mock_response

class TestWeb(unittest.TestCase):

    def setUp(self) -> None:
        self.app = TestApp(create_app())

    def test_index_route(self):
        """Test index page."""
        resp = self.app.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.body.startswith(b'<!DOCTYPE html>'))

    def test_POST(self):
        """Test POST requests -- machine interaction with validator service."""
        manifest_path = "fixtures/3/full_example.json"

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        resp = self.app.post_json(
            "/validate?version=3.0",
            params=manifest,
            status=200,
        )

        data = resp.json
        self.assertIn("okay", data)
        self.assertEqual(data["okay"], 1)

    @patch("presentation_validator.validator.requests.get")
    def test_GET_success(self, mock_get):
        """Test GET requests -- typical user interaction with web form."""
        # Note that attempting to set request.environ['QUERY_STRING'] to mock
        # input data works only the first time. Instead create a new request
        # object to similate each web request, with data that sets request.environ
        mock_get.return_value = mockRequests("fixtures/1/manifest.json")

        resp = self.app.get(
            "/validate",
            params={"url": "http://iiif.io/api/presentation/2.0/example/fixtures/1/manifest.json"}
        )

        self.assertEqual(resp.status_code, 200)

        data = resp.json
        self.assertIn("okay", data)

    @patch("presentation_validator.validator.fetch_manifest")
    def test_GET_missing(self, mock_fetch):
        # Simulate fetch failure
        mock_fetch.side_effect = Exception("Fetch failed")

        resp = self.app.get(
            "/validate",
            params={"url": "http://example.org/a"},
            expect_errors=True  # important if your app returns non-200
        )

        # If your app returns 200 with error JSON:
        self.assertEqual(resp.status_code, 200)

        data = resp.json
        self.assertEqual(data["okay"], 0)
        self.assertTrue(data["error"].startswith("Cannot fetch url"))

    @patch("presentation_validator.validator.requests.get")
    def test_GET_bogus(self, mock_get):
        mock_get.return_value = mockRequests("fixtures/1/manifest.json")

        resp = self.app.get(
            "/validate",
            params={"url": "not_http://a.b.c/"}
        )

        self.assertEqual(resp.status_code, 200)

        data = resp.json
        self.assertIn("okay", data)
        self.assertEqual(data['okay'], 0)

    @patch("presentation_validator.validator.requests.get")
    def test_GET_bogus2(self, mock_get):    
        mock_get.return_value = mockRequests("fixtures/1/manifest.json")

        resp = self.app.get(
            "/validate",
            params={"url": "httpX://a.b/"}
        )

        self.assertEqual(resp.status_code, 200)

        data = resp.json
        self.assertIn("okay", data)
        self.assertEqual(data['okay'], 0)


    @patch("presentation_validator.validator.requests.get")
    def test_GET_accept(self, mock_get):    
        # Check v3 requests pass
        mock_get.return_value = mockRequests("fixtures/3/full_example.json")

        resp = self.app.get(
            "/validate",
            params={
                "url": "https://a.b/",
                "version": "3.0",
                "accept": "true"
            }
        )

        self.assertEqual(resp.status_code, 200)

        data = resp.json
        self.assertIn("okay", data)
        self.assertEqual(data['okay'], 1)

        args, kwargs = mock_get.call_args
        headers = kwargs.get("headers", {})

        self.assertIn("Accept", headers)
        self.assertEqual(headers["Accept"], "application/ld+json;profile=http://iiif.io/api/presentation/3/context.json")

    @patch("presentation_validator.validator.requests.get")
    def test_GET_no_accept(self, mock_get):    
        # Check v3 requests allow accept = false
        mock_get.return_value = mockRequests("fixtures/3/full_example.json")

        resp = self.app.get(
            "/validate",
            params={
                "url": "https://a.b/",
                "version": "3.0",
                "accept": "false"
            }
        )

        self.assertEqual(resp.status_code, 200)

        data = resp.json
        self.assertIn("okay", data)
        self.assertEqual(data['okay'], 1)

        args, kwargs = mock_get.call_args
        headers = kwargs.get("headers", {})

        self.assertNotIn("Accept", headers)

    @patch("presentation_validator.validator.requests.get")
    def test_GET_v2_ask_v3_returned(self, mock_get):    
        # Check v2 requests do not validate v3 manifests
        mock_get.return_value = mockRequests("fixtures/3/full_example.json")

        resp = self.app.get(
            "/validate",
            params={
                "url": "https://a.b/",
                "version": "2.1",
                "accept": "false"
            }
        )

        self.assertEqual(resp.status_code, 200)

        data = resp.json
        self.assertIn("okay", data)
        self.assertEqual(data['okay'], 0)