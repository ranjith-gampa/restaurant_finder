import unittest
from unittest.mock import patch

from app import app


class AppErrorHandlingTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch("app.GooglePlacesClient.from_env")
    def test_runtime_errors_show_generic_message(self, mock_from_env):
        mock_client = mock_from_env.return_value
        mock_client.search_restaurants.side_effect = RuntimeError(
            "Failed to reach Google Maps API. key=secret-key-123"
        )

        response = self.client.get("/?query=vegetarian+restaurants")
        body = response.data.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Unable to fetch restaurant data right now. Please try again.", body)
        self.assertNotIn("secret-key-123", body)


if __name__ == "__main__":
    unittest.main()
