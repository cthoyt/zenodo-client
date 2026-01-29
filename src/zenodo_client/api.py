"""A client for Zenodo."""

from __future__ import annotations

import datetime
import logging
import os
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, Literal, TypeAlias, cast, overload

import pystow
import requests
from tqdm.contrib import tmap
from tqdm.contrib.concurrent import thread_map

from .struct import Metadata
from .version import get_version

__all__ = [
    "Zenodo",
    "create_zenodo",
    "download_all_zenodo",
    "download_zenodo",
    "download_zenodo_latest",
    "ensure_zenodo",
    "publish_zenodo",
    "update_zenodo",
]

logger = logging.getLogger(__name__)

Data = Mapping[str, Any] | Metadata

PartsFunc: TypeAlias = Callable[[str, str, str], Sequence[str]]
PartsHint: TypeAlias = None | Sequence[str] | PartsFunc
Paths: TypeAlias = str | Path | Iterable[str] | Iterable[Path]

TimeoutHint: TypeAlias = int | float

USER_AGENT_NAME = "zenodo-client-python"
USER_AGENT = f"{USER_AGENT_NAME} v{get_version()}"
HEADERS = {
    "User-Agent": USER_AGENT,
}


def ensure_zenodo(key: str, data: Data, paths: Paths, **kwargs: Any) -> requests.Response:
    """Create a Zenodo record if it doesn't exist, or update one that does."""
    return Zenodo(**kwargs).ensure(key=key, data=data, paths=paths)


def create_zenodo(
    data: Data, paths: Paths, *, publish: bool = True, **kwargs: Any
) -> requests.Response:
    """Create a Zenodo record."""
    return Zenodo(**kwargs).create(data, paths, publish=publish)


def update_zenodo(
    deposition_id: str, paths: Paths, *, publish: bool = True, **kwargs: Any
) -> requests.Response:
    """Update a Zenodo record."""
    return Zenodo(**kwargs).update(deposition_id, paths, publish=publish)


def publish_zenodo(deposition_id: str, *, sleep: bool = True, **kwargs: Any) -> requests.Response:
    """Publish a Zenodo record."""
    return Zenodo(**kwargs).publish(deposition_id, sleep=sleep)


def download_zenodo(deposition_id: str, name: str, force: bool = False, **kwargs: Any) -> Path:
    """Download a file from a Zenodo record."""
    return Zenodo(**kwargs).download(deposition_id, name=name, force=force)


def download_all_zenodo(deposition_id: str, force: bool = False, **kwargs: Any) -> list[Path]:
    """Download all files from a Zenodo record."""
    return Zenodo(**kwargs).download_all(deposition_id, force=force)


def download_zenodo_latest(
    deposition_id: str, path: str, force: bool = False, **kwargs: Any
) -> Path:
    """Download the latest Zenodo record."""
    return Zenodo(**kwargs).download_latest(deposition_id, name=path, force=force)


class Zenodo:
    """A wrapper around parts of the Zenodo API."""

    def __init__(self, access_token: str | None = None, sandbox: bool = False) -> None:
        """Initialize the Zenodo class.

        :param access_token: The Zenodo API. Read with :mod:`pystow` from
            zenodo/api_token of zenodo/sandbox_api_token if in sandbox mode.
        :param sandbox: If true, run in the Zenodo sandbox.
        """
        self.sandbox = sandbox
        if self.sandbox:
            self.base = "https://sandbox.zenodo.org"
            # Use subsection support introduced in PyStow in
            # https://github.com/cthoyt/pystow/pull/59
            self.module = "zenodo:sandbox"
            self.access_token = pystow.get_config(
                self.module, "api_token", passthrough=access_token
            )
            if self.access_token is None:
                # old-style fallback
                self.access_token = pystow.get_config(
                    "zenodo", "sandbox_api_token", raise_on_missing=True
                )
        else:
            self.base = "https://zenodo.org"
            self.module = "zenodo"
            self.access_token = pystow.get_config(
                self.module, "api_token", passthrough=access_token, raise_on_missing=True
            )

        # Base URL for the API
        self.api_base = self.base + "/api"
        logger.debug("using Zenodo API at %s", self.api_base)

        # Base URL for depositions, relative to the API base
        self.depositions_base = self.api_base + "/deposit/depositions"

    def ensure(self, key: str, data: Data, paths: Paths) -> requests.Response:
        """Create a Zenodo record if it doesn't exist, or update one that does."""
        deposition_id = pystow.get_config(self.module, key)
        if deposition_id is not None:
            logger.info("mapped local key %s to deposition %s", key, deposition_id)
            return self.update(deposition_id=deposition_id, paths=paths)

        res = self.create(data=data, paths=paths)
        # Write the ID to the key in the local configuration
        # so it doesn't need to be created from scratch next time
        pystow.write_config(self.module, key, str(res.json()["id"]))
        return res

    def create(
        self, data: Data, paths: Paths, *, publish: bool = True, timeout: TimeoutHint = 300
    ) -> requests.Response:
        """Create a record.

        :param data: The JSON data to send to the new data
        :param paths: Paths to local files to upload
        :param publish: Publish the deposit after creation
        :param timeout: How long to timeout on upload?

        :returns: The response JSON from the Zenodo API

        :raises ValueError: if the response is missing a "bucket"
        """
        if isinstance(data, Metadata):
            logger.debug("serializing metadata")
            data = {
                "metadata": {
                    key: value for key, value in data.model_dump(exclude_none=True).items() if value
                },
            }

        res = requests.post(
            self.depositions_base,
            json=data,
            params={"access_token": self.access_token},
            timeout=15,
            headers=HEADERS,
        )
        if res.status_code == 400:
            raise ValueError(res.text)
        res.raise_for_status()

        res_json = res.json()
        bucket = res_json.get("links", {}).get("bucket")
        if bucket is None:
            raise ValueError(f"No bucket in response. Got: {res_json}")

        logger.info("uploading files to bucket %s", bucket)
        self._upload_files(bucket=bucket, paths=paths, timeout=timeout)

        deposition_id = res_json["id"]
        if not publish:
            return self._get_deposition(deposition_id)

        logger.info("publishing files to deposition %s", deposition_id)
        return self.publish(deposition_id)

    def edit(self, deposition_id: str, sleep: bool = True) -> requests.Response:
        """Unlock already submitted deposition for editing, see https://developers.zenodo.org/#edit.

        :param deposition_id: The identifier of the deposition on Zenodo.
        :param sleep: Sleep for one second just in case of race conditions. If you're
            feeling lucky and rushed, you might be able to get away with disabling this.

        :returns: The response JSON from the Zenodo API
        """
        return self._action(deposition_id=deposition_id, action="edit", sleep=sleep)

    def publish(self, deposition_id: str, sleep: bool = True) -> requests.Response:
        """Publish a record that's in edit mode, see https://developers.zenodo.org/#publish.

        :param deposition_id: The identifier of the deposition on Zenodo.
        :param sleep: Sleep for one second just in case of race conditions. If you're
            feeling lucky and rushed, you might be able to get away with disabling this.

        :returns: The response JSON from the Zenodo API
        """
        return self._action(deposition_id=deposition_id, action="publish", sleep=sleep)

    def discard(self, deposition_id: str, sleep: bool = True) -> requests.Response:
        """Discard changes in the current editing session., see https://developers.zenodo.org/#discard.

        :param deposition_id: The identifier of the deposition on Zenodo.
        :param sleep: Sleep for one second just in case of race conditions. If you're
            feeling lucky and rushed, you might be able to get away with disabling this.

        :returns: The response JSON from the Zenodo API
        """
        return self._action(deposition_id=deposition_id, action="discard", sleep=sleep)

    def new_version(self, deposition_id: str, sleep: bool = True) -> requests.Response:
        """Create a new version of a deposition, see https://developers.zenodo.org/#new-version.

        :param deposition_id: The identifier of the deposition on Zenodo.
        :param sleep: Sleep for one second just in case of race conditions. If you're
            feeling lucky and rushed, you might be able to get away with disabling this.

        :returns: The response JSON from the Zenodo API
        """
        return self._action(deposition_id=deposition_id, action="newversion", sleep=sleep)

    def _action(
        self,
        deposition_id: str,
        action: Literal["discard", "publish", "newversion", "edit"],
        sleep: bool = True,
    ) -> requests.Response:
        """Run an action on a record.

        :param deposition_id: The identifier of the deposition on Zenodo. It should be
            in edit mode.
        :param action: The action to perform
        :param sleep: Sleep for one second just in case of race conditions. If you're
            feeling lucky and rushed, you might be able to get away with disabling this.

        :returns: The response JSON from the Zenodo API
        """
        if sleep:
            time.sleep(1)
        res = requests.post(
            f"{self.depositions_base}/{deposition_id}/actions/{action}",
            params={"access_token": self.access_token},
            timeout=15,
            headers=HEADERS,
        )
        res.raise_for_status()
        return res

    def _get_deposition(self, deposition_id: str) -> requests.Response:
        """Get the metadata for a deposition."""
        url = f"{self.depositions_base}/{deposition_id}"
        res = requests.get(
            url, params={"access_token": self.access_token}, timeout=5, headers=HEADERS
        )
        res.raise_for_status()
        return res

    def update(
        self, deposition_id: str, paths: Paths, *, publish: bool = True, timeout: TimeoutHint = 300
    ) -> requests.Response:
        """Update a record, including creating a new version, with the given files.

        :param deposition_id: The identifier of the deposition on Zenodo.
        :param paths: Paths to local files to upload; existing files with matching
            hashes will not be uploaded.
        :param publish: Publish the deposition after the update.
        :param timeout: The maximum timeout for uploading files

        :returns: The response JSON from the Zenodo API
        """
        res = self._get_deposition(deposition_id)

        deposition_data = res.json()
        if deposition_data["submitted"]:
            new_deposition_id, new_deposition_data = self._update_submitted_deposition_metadata(
                deposition_id
            )
        else:
            new_deposition_id, new_deposition_data = deposition_data["id"], deposition_data

        bucket = new_deposition_data["links"]["bucket"]

        # Upload new files. It calculates the hash on all of these, and if no files have changed,
        #  there will be no update
        self._upload_files(bucket=bucket, paths=paths, timeout=timeout)

        # Get the new metadata with the files
        res = self._get_deposition(deposition_id)

        if not publish:
            # Return the response with latest metadata
            return res

        # Send the publish command
        return self.publish(new_deposition_id)

    def _update_submitted_deposition_metadata(
        self, deposition_id: str
    ) -> tuple[str, dict[str, Any]]:
        res = self._get_deposition(deposition_id)
        old_version = res.json()["metadata"]["version"]
        new_version = _prepare_new_version(old_version)

        res = self.new_version(deposition_id, sleep=False)
        # Parse out the new version (@zenodo please give this as its own field!)
        new_deposition_id = res.json()["links"]["latest_draft"].split("/")[-1]

        # Get all metadata associated with the new version (this has updated DOIs, etc.)
        # see: https://developers.zenodo.org/#retrieve
        res = requests.get(
            f"{self.depositions_base}/{new_deposition_id}",
            params={"access_token": self.access_token},
            timeout=15,
            headers=HEADERS,
        )
        res.raise_for_status()
        new_deposition_data = res.json()
        # Update the version and date
        new_deposition_data["metadata"]["version"] = new_version
        new_deposition_data["metadata"]["publication_date"] = datetime.datetime.today().strftime(
            "%Y-%m-%d"
        )

        # Update the deposition for the new version
        # see: https://developers.zenodo.org/#update
        res = requests.put(
            f"{self.depositions_base}/{new_deposition_id}",
            json={"metadata": new_deposition_data["metadata"]},
            params={"access_token": self.access_token},
            timeout=15,
            headers=HEADERS,
        )
        res.raise_for_status()

        return new_deposition_id, new_deposition_data

    def _upload_files(
        self, *, bucket: str, paths: Paths, timeout: TimeoutHint
    ) -> list[requests.Response]:
        _paths = [paths] if isinstance(paths, str | Path) else paths
        rv = []
        # see https://developers.zenodo.org/#quickstart-upload
        for path in _paths:
            with open(path, "rb") as file:
                res = requests.put(
                    f"{bucket}/{os.path.basename(path)}",
                    data=file,
                    params={"access_token": self.access_token},
                    timeout=timeout,
                )

            res.raise_for_status()
            rv.append(res)
        return rv

    def get_record(self, record_id: int | str, *, authenticate: bool = True) -> requests.Response:
        """Get the metadata for a given record.

        :param record_id: The identifier of the Zenodo record.
        :param authenticate: Whether to use an access token for authentication

        :returns: The response JSON from the Zenodo API
        """
        params = {}
        if authenticate:
            params["access_token"] = self.access_token
        res = requests.get(
            f"{self.api_base}/records/{record_id}",
            params=params,
            timeout=5,
            headers=HEADERS,
        )
        res.raise_for_status()
        return res

    def get_latest_record(self, record_id: int | str, *, authenticate: bool = True) -> str:
        """Get the latest record related to the given record.

        :param record_id: The identifier of the Zenodo record.
        :param authenticate: Whether to use an access token for authentication

        :returns: The ID of the latest record related to the given one
        """
        res_json = self.get_record(record_id, authenticate=authenticate).json()
        # Still works even in the case that the given record ID is the latest.
        latest = cast(str, res_json["links"]["latest"].split("/")[-3])
        logger.debug("latest for zenodo.record:%s is zenodo.record:%s", record_id, latest)
        return latest

    def download(
        self, record_id: int | str, name: str, *, force: bool = False, parts: PartsHint = None
    ) -> Path:
        """Download the file for the given record.

        :param record_id: The Zenodo record id
        :param name: The name of the file in the Zenodo record
        :param parts: Optional arguments on where to store with :func:`pystow.ensure`.
            If none given, goes in
            ``<PYSTOW_HOME>/zenodo/<CONCEPT_RECORD_ID>/<RECORD>/<PATH>``. Where
            ``CONCEPT_RECORD_ID`` is the consistent concept record ID for all versions
            of the same record. If a function is given, the function should take 3
            position arguments: concept record id, record id, and version, then return a
            sequence for PyStow. The name of the file is automatically appended to the
            end of the sequence.
        :param force: Should the file be re-downloaded if it already is cached? Defaults
            to false.

        :returns: the path to the downloaded file.

        :raises FileNotFoundError: If the Zenodo record doesn't have a file with the
            given name

        For example, to download the most recent version of NSoC-KG, you can use the
        following command:

        .. code-block:: python

            path = Zenodo().download("4574555", "triples.tsv")

        Even as new versions of the data are uploaded, this command will always be able
        to check if a new version is available, download it if it is, and return the
        local file path. If the most recent version is already downloaded, then it
        returns the local file path to the cached file.

        The file path uses :mod:`pystow` under the ``zenodo`` module and uses the
        "concept record ID" as a submodule since that is the consistent identifier
        between different records that are versions of the same data.
        """
        return self._download_helper(record_id, name=name, force=force, parts=parts)

    def download_all(
        self, record_id: int | str, *, force: bool = False, parts: PartsHint = None
    ) -> list[Path]:
        """Download all files for the given record."""
        return self._download_helper(record_id, name=None, force=force, parts=parts)

    @overload
    def _download_helper(
        self, record_id: int | str, *, name: str = ..., force: bool = ..., parts: PartsHint = ...
    ) -> Path: ...

    @overload
    def _download_helper(
        self, record_id: int | str, *, name: None = ..., force: bool = ..., parts: PartsHint = ...
    ) -> list[Path]: ...

    def _download_helper(
        self,
        record_id: int | str,
        *,
        name: str | None = None,
        force: bool = False,
        parts: PartsHint = None,
        concurrent: bool = True,
    ) -> Path | list[Path]:
        """Download all files from a given record."""
        res_json = self.get_record(record_id).json()
        # conceptrecid is the consistent record ID for all versions of the same record
        concept_record_id = res_json["conceptrecid"]
        # FIXME send error report to zenodo about this - shouldn't version be required?
        version = res_json["metadata"].get("version", "v1")
        logger.debug("version for zenodo.record:%s is %s", record_id, version)

        if parts is None:
            parts = [self.module.replace(":", "-"), concept_record_id, version]
        elif callable(parts):
            parts = parts(concept_record_id, str(record_id), version)

        name_url_pairs: list[tuple[str, str]] = [
            (file["key"], file["links"]["self"]) for file in res_json["files"]
        ]

        if name is None:

            def _func(name_url: tuple[str, str]) -> Path:
                return pystow.ensure(*parts, name=name_url[0], url=name_url[1], force=force)

            if concurrent:
                return thread_map(_func, name_url_pairs)
            else:
                return list(tmap(_func, name_url_pairs))

        rv = [
            pystow.ensure(*parts, name=n, url=url, force=force)
            for n, url in name_url_pairs
            if n == name
        ]
        if not rv:
            raise FileNotFoundError(
                f"zenodo.record:{record_id} does not have a file with key {name}"
            )

        return rv[0]

    def download_latest(
        self,
        record_id: int | str,
        name: str,
        *,
        force: bool = False,
        parts: PartsHint = None,
    ) -> Path:
        """Download the latest version of the file."""
        latest_record_id = self.get_latest_record(record_id)
        return self.download(latest_record_id, name=name, force=force, parts=parts)


def _prepare_new_version(old_version: str) -> str:
    # FIXME handle if original version wasn't a date
    new_version = datetime.datetime.today().strftime("%Y-%m-%d")
    if old_version == new_version:
        new_version += "-1"
    elif (
        old_version.startswith(new_version)
        and old_version[-2] == "-"
        and old_version[-1].isnumeric()
    ):
        new_version += "-" + str(
            1 + int(old_version[-1])
        )  # please don't do this more than 10 times a day
    return new_version
