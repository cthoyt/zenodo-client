"""Tests for the upload and revision lifecyle."""

import logging
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

import pystow

from zenodo_client import Creator, Metadata, Zenodo
from zenodo_client.struct import _today_str

logger = logging.getLogger(__name__)

TEXT_V1 = "this is some test text\noh yeah baby"
TEXT_V2 = "this is some v2 test text\noh yeah baby"
TEXT_V3 = "this is some v3 test text\noh yeah baby"

ACCESS_TOKEN = pystow.get_config("zenodo", "sandbox_api_token")


@unittest.skipUnless(ACCESS_TOKEN, reason="Missing Zenodo sandbox API token")
class TestLifecycle(unittest.TestCase):
    """Test case for zenodo client."""

    def setUp(self) -> None:
        """Set up the test case with a zenodo client."""
        self.zenodo = Zenodo(sandbox=True, access_token=ACCESS_TOKEN)
        self.key = f"test-{uuid4()}"
        self._directory = tempfile.TemporaryDirectory()
        self.directory = Path(self._directory.name).resolve()

    def tearDown(self) -> None:
        """Tear down the test case."""
        self._directory.cleanup()

    def test_create(self):
        """Test creating a record."""
        data = Metadata(
            title="Test Upload",
            upload_type="dataset",
            description="test description",
            creators=[
                Creator(
                    name="Hoyt, Charles Tapley",
                    affiliation="Harvard Medical School",
                    orcid="0000-0003-4423-4370",
                ),
            ],
        )
        path = self.directory.joinpath("test.txt")
        path.write_text(TEXT_V1)

        logger.info(f"wrote data to {path}")
        res = self.zenodo.ensure(
            key=self.key,
            data=data,
            paths=path,
        )
        res_json = res.json()
        # print(f"\n\nSEE V1 ON ZENODO: {res_json['links']['record_html']}")

        self.assertEqual(True, res_json["submitted"])
        self.assertEqual("done", res_json["state"])
        self.assertEqual("dataset", res_json["metadata"]["upload_type"])
        self.assertEqual(data.title, res_json["metadata"]["title"])
        self.assertEqual(data.version, res_json["metadata"]["version"])

        deposition_id = res_json["record_id"]
        # print(f"DEPOSITION ID: {deposition_id}")
        path.write_text(TEXT_V2)

        res = self.zenodo.update(deposition_id, paths=path)
        res_json = res.json()
        # print(f"SEE V2 ON ZENODO: {res_json['links']['record_html']}")
        self.assertEqual(f"{data.version}-1", res_json["metadata"]["version"])

        path.write_text(TEXT_V3)
        res = self.zenodo.update(deposition_id, paths=path)
        res_json = res.json()
        print(f"SEE V3 ON ZENODO: {res_json['links']['record_html']}")
        self.assertEqual(f"{today}-2", res_json["metadata"]["version"])
