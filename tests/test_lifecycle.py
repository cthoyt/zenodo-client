"""Tests for the upload and revision lifecyle."""

import logging
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

import pystow

from zenodo_client import Creator, Metadata, Zenodo

logger = logging.getLogger(__name__)

TEXT_V1 = "this is some test text\noh yeah baby"
TEXT_V2 = "this is some v2 test text\noh yeah baby"
TEXT_V3 = "this is some v3 test text\noh yeah baby"

ACCESS_TOKEN = pystow.get_config("zenodo", "sandbox_api_token") or pystow.get_config("zenodo:sandbox", "api_token")


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
        # print(f"SEE V3 ON ZENODO: {res_json['links']['record_html']}")
        self.assertEqual(f"{data.version}-2", res_json["metadata"]["version"])

    def test_metadata_fields(self):
        """Test metadata fields."""
        data = Metadata(
            title="Test Upload",
            upload_type="publication",
            description="test description",
            creators=[
                Creator(
                    name="Hoyt, Charles Tapley",
                    affiliation="Harvard Medical School",
                    orcid="0000-0003-4423-4370",
                    gnd="1203140533",
                ),
            ],
            access_right="embargoed",
            language="ger",
            version="ver1",
            license="my-own-license",
            publication_type="patent",
            #image_type="figure",
            communities=["zenodo", "bioinformatics"],
            keywords=["key1", "key2", "key3"],
            notes="this is important",
        )
        path = self.directory.joinpath("test.txt")
        path.write_text(TEXT_V1)

        res = self.zenodo.ensure(
            key=self.key,
            data=data,
            paths=path,
        )
        res_json = res.json()

        self.assertEqual(data.title, res_json["metadata"]["title"])
        self.assertEqual(data.upload_type, res_json["metadata"]["upload_type"])
        self.assertEqual(data.description, res_json["metadata"]["description"])
        self.assertEqual(len(data.creators), len(res_json["metadata"]["creators"]))
        self.assertEqual(data.access_right, res_json["metadata"]["access_right"])
        self.assertEqual(data.language, res_json["metadata"]["language"])
        self.assertEqual(data.version, res_json["metadata"]["version"])
        self.assertEqual(data.license, res_json["metadata"]["license"])
        self.assertEqual(data.publication_type, res_json["metadata"]["publication_type"])
        self.assertEqual(len(data.communities), len(res_json["metadata"]["communities"]))
        self.assertEqual(data.communities[1], res_json["metadata"]["communities"][1]["id"])
        self.assertEqual(data.keywords, res_json["metadata"]["keywords"])
        self.assertEqual(data.notes, res_json["metadata"]["notes"])

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
