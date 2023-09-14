"""Tests for the upload and revision lifecyle."""

import logging
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

import requests

from zenodo_client import Creator, Metadata, Zenodo

logger = logging.getLogger(__name__)

TEXT_V1 = "this is some test text\noh yeah baby"
TEXT_V2 = "this is some v2 test text\noh yeah baby"
TEXT_V3 = "this is some v3 test text\noh yeah baby"

CREATOR = Creator(
    name="Hoyt, Charles Tapley",
    affiliation="Northeastern University",
    orcid="0000-0003-4423-4370",
    # Note: zenodo has some problem validating my GND. Skip it for now
    # gnd="1203140533",
)


class TestLifecycle(unittest.TestCase):
    """Test case for zenodo client."""

    def setUp(self) -> None:
        """Set up the test case with a zenodo client."""
        self.zenodo = Zenodo(sandbox=True)
        self.key = f"test-{uuid4()}"
        self._directory = tempfile.TemporaryDirectory()
        self.directory = Path(self._directory.name).resolve()

        self.path = self.directory.joinpath("test.txt")
        self.path.write_text(TEXT_V1)

    def tearDown(self) -> None:
        """Tear down the test case."""
        self._directory.cleanup()

    def test_connect(self):
        """Test connection works."""
        r = requests.get(self.zenodo.depositions_base, params={"access_token": self.zenodo.access_token})
        self.assertEqual(200, r.status_code, msg=r.text)

    def test_create(self):
        """Test creating a record."""
        data = Metadata(
            title="Test Upload",
            upload_type="dataset",
            description="test description",
            creators=[CREATOR],
        )

        res = self.zenodo.ensure(key=self.key, data=data, paths=self.path)
        res_json = res.json()
        # print(f"\n\nSEE V1 ON ZENODO: {res_json['links']['record_html']}")
        self.assertEqual(True, res_json["submitted"])
        self.assertEqual("done", res_json["state"])
        self.assertEqual("dataset", res_json["metadata"]["upload_type"])
        self.assertEqual(data.title, res_json["metadata"]["title"])
        self.assertEqual(data.version, res_json["metadata"]["version"])

        deposition_id = res_json["record_id"]
        # print(f"DEPOSITION ID: {deposition_id}")
        self.path.write_text(TEXT_V2)

        res = self.zenodo.update(deposition_id, paths=self.path)
        res_json = res.json()
        # print(f"SEE V2 ON ZENODO: {res_json['links']['record_html']}")
        self.assertEqual(f"{data.version}-1", res_json["metadata"]["version"])

        self.path.write_text(TEXT_V3)
        res = self.zenodo.update(deposition_id, paths=self.path)
        res_json = res.json()
        # print(f"SEE V3 ON ZENODO: {res_json['links']['record_html']}")
        self.assertEqual(f"{data.version}-2", res_json["metadata"]["version"])

    def test_create_no_orcid(self):
        """Test create with no ORCID."""
        data = Metadata(
            title="Test Upload",
            upload_type="dataset",
            description="test description",
            creators=[
                Creator(
                    name="Hoyt, Charles Tapley",
                    affiliation="Harvard Medical School",
                ),
            ],
        )

        res = self.zenodo.ensure(key=self.key, data=data, paths=self.path)
        res_json = res.json()
        # print(f"\n\nSEE V1 ON ZENODO: {res_json['links']['record_html']}")
        self.assertEqual(True, res_json["submitted"])
        self.assertEqual("done", res_json["state"])
        self.assertEqual("dataset", res_json["metadata"]["upload_type"])
        self.assertEqual(data.title, res_json["metadata"]["title"])
        self.assertEqual(data.version, res_json["metadata"]["version"])
