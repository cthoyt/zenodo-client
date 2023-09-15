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


class TestLifecycle(unittest.TestCase):
    """Test case for zenodo client."""

    def setUp(self) -> None:
        """Set up the test case with a zenodo client."""
        self.zenodo = Zenodo(sandbox=True)
        self.assertIsInstance(self.zenodo.access_token, str)
        self.assertNotEqual("", self.zenodo.access_token, msg="Zenodo sandbox API token was set to empty string")

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
            upload_type="publication",
            description="test description",
            creators=[CREATOR],
            access_right="embargoed",
            embargo_date=(datetime.date.today() + datetime.timedelta(days=5)).strftime("%Y-%m-%d"),
            language="eng",
            # version="ver1",
            license="CC-BY-4.0",
            publication_type="patent",
            # image_type="figure",
            communities=[Community(identifier="zenodo"), Community(identifier="bioinformatics")],
            keywords=["key1", "key2", "key3"],
            notes="this is important",
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
        self.assertEqual({"zenodo", "bioinformatics"}, {c["identifier"] for c in res_json["metadata"]["communities"]})
        self.assertEqual(data.keywords, res_json["metadata"]["keywords"])
        self.assertEqual(data.notes, res_json["metadata"]["notes"])

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

    def test_create_without_publish(self):
        """Test create without publishing."""
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

        res = self.zenodo.create(data=data, paths=[], publish=False)
        res_create_json = res.json()

        self.assertEqual(False, res_create_json["submitted"])
        self.assertEqual("unsubmitted", res_create_json["state"])
        self.assertEqual(0, len(res_create_json["files"]))

    def test_update_with_metadata_publish(self):
        """Test seperating creation, uploading, updating, and publishing."""
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

        res = self.zenodo.create(data=data, paths=[], publish=False)
        res_create_json = res.json()
        deposition_id = res_create_json["id"]

        self.assertEqual(False, res_create_json["submitted"])
        self.assertEqual("unsubmitted", res_create_json["state"])
        self.assertEqual(0, len(res_create_json["files"]))

        path = self.directory.joinpath("test.txt")
        expected_doi = res_create_json["metadata"]["prereserve_doi"]["doi"]
        path.write_text("DOI: https://doi.org/%s" % expected_doi)

        # update files before publish
        res = self.zenodo.update(deposition_id=deposition_id, paths=[path], publish=False)
        res_update_json = res.json()
        self.assertEqual(False, res_update_json["submitted"])
        self.assertEqual("unsubmitted", res_update_json["state"])
        self.assertEqual(data.title, res_update_json["metadata"]["title"])
        self.assertEqual(data.version, res_update_json["metadata"]["version"])
        self.assertEqual(1, len(res_update_json["files"]))
        self.assertEqual("test.txt", res_update_json["files"][0]["filename"])

        data.title = "Test Publication with Metadata Update"
        res = self.zenodo.update_metadata(deposition_id=deposition_id, data=data, publish=True)
        res_update_metadata_json = res.json()
        self.assertEqual(True, res_update_metadata_json["submitted"])
        self.assertEqual("done", res_update_metadata_json["state"])
        self.assertEqual(expected_doi, res_update_metadata_json["doi"])
        self.assertEqual(data.title, res_update_metadata_json["metadata"]["title"])

    def test_multi_step_publish(self):
        """Test separate steps of creation, upload, and publishing."""
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
        path.write_text("it's just the beginning")

        res = self.zenodo.create(data=data, paths=[path], publish=False)
        res_create_json = res.json()
        deposition_id = res_create_json["id"]
        path_hash = hashlib.md5(path.read_bytes()).hexdigest()  # noqa:S324,S303
        self.assertEqual(path_hash, res_create_json["files"][0]["checksum"])

        data.title = "Test Upload with an Update to Unpublished Deposition"

        path_2 = self.directory.joinpath("test2.txt")
        path_2.write_text("it's all metadata after this")
        res = self.zenodo.update(deposition_id=deposition_id, paths=[path_2], publish=False)
        res_update_json = res.json()

        self.assertEqual(False, res_update_json["submitted"])
        self.assertEqual("unsubmitted", res_update_json["state"])
        self.assertEqual(2, len(res_update_json["files"]))
        self.assertEqual("test.txt", res_update_json["files"][1]["filename"])
        self.assertEqual("test2.txt", res_update_json["files"][0]["filename"])

        path_hash_2 = hashlib.md5(path_2.read_bytes()).hexdigest()  # noqa:S324,S303
        self.assertEqual(path_hash_2, res_update_json["files"][0]["checksum"])

        data.title = "Test Publication with Metadata Update"
        res = self.zenodo.update_metadata(deposition_id=deposition_id, data=data, publish=True)
        res_update_metadata_json = res.json()

        self.assertEqual(True, res_update_metadata_json["submitted"])
        self.assertEqual("done", res_update_metadata_json["state"])
        self.assertEqual(data.title, res_update_metadata_json["metadata"]["title"])

    def test_update_metadata(self):
        """Test updating (partial) metadata with/without new versions."""
        data = Metadata(
            title="Test Metadata",
            upload_type="dataset",
            description="test description",
            publication_date="2022-02-22",
            creators=[
                Creator(
                    name="Hoyt, Charles Tapley",
                    affiliation="Harvard Medical School",
                    orcid="0000-0003-4423-4370",
                ),
            ],
            version="v1",
        )
        path = self.directory.joinpath("test.txt")
        path.write_text("it's all metadata after this")

        res = self.zenodo.create(data=data, paths=[path])
        res_create_json = res.json()
        deposition_id = res_create_json["id"]

        self.assertEqual(data.version, res_create_json["metadata"]["version"])

        new_data = Metadata(
            title="New and better Test Metadata",
            upload_type=data.upload_type,
            description=data.description,
            creators=data.creators,
        )

        res = self.zenodo.update_metadata(deposition_id=deposition_id, data=new_data)
        res_update_json = res.json()
        deposition_id = res_update_json["id"]

        self.assertEqual(True, res_update_json["submitted"])
        self.assertEqual("done", res_update_json["state"])
        self.assertEqual(
            data.description, res_update_json["metadata"]["description"]
        )  # unchanged, but must still be present
        self.assertEqual(new_data.title, res_update_json["metadata"]["title"])
        self.assertEqual(data.version, res_create_json["metadata"]["version"])

        new_data.upload_type = "poster"
        new_data.version = "v2.3"

        res = self.zenodo.update_metadata(deposition_id=deposition_id, data=new_data, publish=False)
        res_update_json = res.json()
        deposition_id = res_update_json["id"]

        self.assertEqual(True, res_update_json["submitted"])
        self.assertEqual("inprogress", res_update_json["state"])
        self.assertEqual(new_data.upload_type, res_update_json["metadata"]["upload_type"])
        self.assertEqual(new_data.version, res_update_json["metadata"]["version"])

        res = self.zenodo.update_metadata(deposition_id=deposition_id, data=new_data, publish=True)
        res_update_json = res.json()
        deposition_id = res_update_json["id"]

        self.assertEqual(True, res_update_json["submitted"])
        self.assertEqual("done", res_update_json["state"])
        self.assertEqual(new_data.version, res_update_json["metadata"]["version"])
