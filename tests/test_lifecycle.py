"""Tests for the upload and revision lifecyle."""

import datetime
import hashlib
import logging
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

import requests

from zenodo_client import Creator, Metadata, Zenodo
from zenodo_client.struct import Community

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


class TestStruct(unittest.TestCase):
    """Tests for data structures."""

    def test_name(self) -> None:
        """Test name errors."""
        with self.assertRaises(ValueError):
            Creator(name="Charles Tapley Hoyt")


class TestLifecycle(unittest.TestCase):
    """Test case for zenodo client."""

    def setUp(self) -> None:
        """Set up the test case with a zenodo client."""
        self.zenodo = Zenodo(sandbox=True)
        self.assertIsInstance(self.zenodo.access_token, str)
        self.assertNotEqual(
            "", self.zenodo.access_token, msg="Zenodo sandbox API token was set to empty string"
        )

        self.key = f"test-{uuid4()}"
        self._directory = tempfile.TemporaryDirectory()
        self.directory = Path(self._directory.name).resolve()

        self.path = self.directory.joinpath("test.txt")
        self.path.write_text(TEXT_V1)

    def tearDown(self) -> None:
        """Tear down the test case."""
        self._directory.cleanup()

    def test_connect(self) -> None:
        """Test connection works."""
        r = requests.get(
            self.zenodo.depositions_base,
            params={"access_token": self.zenodo.access_token},
            timeout=5,
        )
        self.assertEqual(200, r.status_code, msg=r.text)

    def test_create(self) -> None:
        """Test creating a record."""
        data = Metadata(
            title="Test Upload",
            upload_type="publication",
            description="test description",
            creators=[CREATOR],
            access_right="embargoed",
            embargo_date=(datetime.date.today() + datetime.timedelta(days=5)).strftime("%Y-%m-%d"),
            language="eng",
            # version="ver1",
            license="cc-by-4.0",
            publication_type="patent",
            # image_type="figure",
            communities=[Community(identifier="zenodo"), Community(identifier="bioinformatics")],
            keywords=["key1", "key2", "key3"],
            notes="this is important",
        )
        self.assertIsNotNone(
            data.version, msg="When not given, version should be set to today's date"
        )

        res = self.zenodo.ensure(key=self.key, data=data, paths=self.path)
        res_json = res.json()
        # print(f"\n\nSEE V1 ON ZENODO: {res_json['links']['record_html']}")
        self.assertEqual(True, res_json["submitted"])
        self.assertEqual("done", res_json["state"])
        self.assertEqual("publication", res_json["metadata"]["upload_type"])
        self.assertEqual(data.title, res_json["metadata"]["title"])
        self.assertEqual(data.version, res_json["metadata"]["version"])
        self.assertEqual(data.description, res_json["metadata"]["description"])
        self.assertEqual(len(data.creators), len(res_json["metadata"]["creators"]))
        self.assertEqual(data.access_right, res_json["metadata"]["access_right"])
        self.assertEqual(data.language, res_json["metadata"]["language"])
        self.assertEqual(data.license, res_json["metadata"]["license"])
        self.assertEqual(data.publication_type, res_json["metadata"]["publication_type"])
        # FIXME bug in new zenodo - communities are not returned by creation endpoint
        # self.assertIn(
        #     "communities", res_json["metadata"], msg=f"\nKeys: {set(res_json['metadata'])}"
        # )
        # self.assertEqual(
        #     {"zenodo", "bioinformatics"},
        #     {c["identifier"] for c in res_json["metadata"]["communities"]},
        # )
        self.assertEqual(data.keywords, res_json["metadata"]["keywords"])
        self.assertEqual(data.notes, res_json["metadata"]["notes"])

        deposition_v1_id = str(res_json["record_id"])
        # print(f"DEPOSITION ID: {deposition_id}")
        self.path.write_text(TEXT_V2)

        res_v2 = self.zenodo.update(deposition_v1_id, paths=self.path)
        res_v2_json = res_v2.json()
        deposition_v2_id = res_v2_json["id"]
        # print(f"SEE V2 ON ZENODO: {res_json['links']['record_html']}")
        self.assertNotEqual(deposition_v1_id, deposition_v2_id)
        self.assertEqual(f"{data.version}-1", res_v2_json["metadata"]["version"])

        self.path.write_text(TEXT_V3)
        res_v3 = self.zenodo.update(deposition_v2_id, paths=self.path)
        res_v3_json = res_v3.json()
        # print(f"SEE V3 ON ZENODO: {res_json['links']['record_html']}")
        self.assertNotEqual(deposition_v1_id, res_v3_json["id"])
        self.assertNotEqual(deposition_v2_id, res_v3_json["id"])
        self.assertEqual(f"{data.version}-2", res_v3_json["metadata"]["version"])

    def test_create_no_orcid(self) -> None:
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

    def test_create_without_publish(self) -> None:
        """Test create without publishing."""
        data = Metadata(
            title="Test Upload",
            upload_type="dataset",
            description="Test create without publishing",
            creators=[
                Creator(
                    name="Hoyt, Charles Tapley",
                    affiliation="Harvard Medical School",
                    orcid="0000-0003-4423-4370",
                ),
            ],
        )

        res = self.zenodo.create(data=data, paths=[], publish=False)
        res_create_json = res.json()
        deposition_id = res_create_json["id"]

        self.assertEqual(False, res_create_json["submitted"])
        self.assertEqual("unsubmitted", res_create_json["state"])
        self.assertEqual(0, len(res_create_json["files"]))

        path = self.directory.joinpath("doi.txt")
        path.write_text(
            "this record will have DOI {}".format(
                res_create_json["metadata"]["prereserve_doi"]["doi"]
            )
        )

        res = self.zenodo.update(deposition_id, paths=[path], publish=False)
        res_update_json = res.json()

        path_hash = hashlib.md5(path.read_bytes()).hexdigest()  # noqa: S324
        self.assertEqual(path_hash, res_update_json["files"][0]["checksum"])
        self.assertEqual(deposition_id, res_update_json["id"])

        res = self.zenodo.publish(deposition_id=deposition_id)
        res_publish_json = res.json()
        self.assertEqual(deposition_id, res_publish_json["id"])
