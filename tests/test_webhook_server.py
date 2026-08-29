import json
import time
import unittest
from urllib import request

from shusha.models.webhook_server import WebhookServer


class TestWebhookServer(unittest.TestCase):
    def setUp(self):
        self.received_payloads = []
        self.server = WebhookServer(
            host="127.0.0.1",
            port=6819,  # Use test port
            on_download_received=lambda payload: self.received_payloads.append(payload),
        )
        self.started = self.server.start()
        time.sleep(0.1)

    def tearDown(self):
        self.server.stop()
        time.sleep(0.05)

    def test_health_check_endpoint(self):
        if not self.started:
            self.skipTest("WebhookServer could not bind to port")

        req = request.Request("http://127.0.0.1:6819/health", method="GET")
        with request.urlopen(req, timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)
            body = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(body.get("status"), "online")
            self.assertEqual(body.get("app"), "Shusha-DM")

    def test_add_download_post_endpoint(self):
        if not self.started:
            self.skipTest("WebhookServer could not bind to port")

        payload = {
            "url": "https://example.com/file.zip",
            "filename": "custom_file.zip",
            "headers": {"User-Agent": "Mozilla/5.0"},
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            "http://127.0.0.1:6819/add",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with request.urlopen(req, timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)
            res = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(res.get("status"), "success")

        time.sleep(0.05)
        self.assertEqual(len(self.received_payloads), 1)
        self.assertEqual(
            self.received_payloads[0]["url"], "https://example.com/file.zip"
        )


if __name__ == "__main__":
    unittest.main()
