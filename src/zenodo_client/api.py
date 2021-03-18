# -*- coding: utf-8 -*-

"""A client for Zenodo."""

import datetime
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence, Union

import pystow
import requests

from .struct import Metadata

__all__ = [
    'ensure_zenodo',
    'update_zenodo',
    'create_zenodo',
    'Zenodo',
]

logger = logging.getLogger(__name__)

Data = Union[Mapping[str, Any], Metadata]

PartsFunc = Callable[[str, str, str], Sequence[str]]
PartsHint = Union[None, Sequence[str], PartsFunc]


def ensure_zenodo(key: str, data: Data, paths: Union[str, Iterable[str]], **kwargs) -> requests.Response:
    """Create a Zenodo record if it doesn't exist, or update one that does."""
    deposition_id = pystow.get_config('zenodo', key)
    if deposition_id is not None:
        return update_zenodo(deposition_id, paths, **kwargs)

    res = create_zenodo(data, paths, **kwargs)
    # Write the ID to the key in the local configuration
    # so it doesn't need to be created from scratch next time
    pystow.write_config('zenodo', key, str(res.json()['id']))
    return res


def create_zenodo(data: Data, paths: Union[str, Iterable[str]], **kwargs) -> requests.Response:
    """Create a Zenodo record."""
    return Zenodo(**kwargs).create(data, paths)


def update_zenodo(deposition_id: str, paths: Union[str, Iterable[str]], **kwargs) -> requests.Response:
    """Update a Zenodo record."""
    return Zenodo(**kwargs).update(deposition_id, paths)


class Zenodo:
    """A wrapper around parts of the Zenodo API."""

    def __init__(self, access_token: Optional[str] = None, sandbox: bool = False):
        """Initialize the Zenodo class.

        :param access_token: The Zenodo API. Read with :mod:`pystow` from zenodo/api_token
            of zenodo/sandbox_api_token if in sandbox mode.
        :param sandbox: If true, run in the Zenodo sandbox.
        """
        self.sandbox = sandbox
        if self.sandbox:
            self.base = 'https://sandbox.zenodo.org/api'
            self.token_key = 'sandbox_api_token'
        else:
            self.base = 'https://zenodo.org/api'
            self.token_key = 'api_token'

        # Base URL for depositions, relative to the API base
        self.depositions_base = self.base + '/deposit/depositions'

        self.access_token = access_token or pystow.get_config('zenodo', self.token_key)

    def create(self, data: Data, paths: Union[str, Iterable[str]]) -> requests.Response:
        """Create a record.

        :param data: The JSON data to send to the new data
        :param paths: Paths to local files to upload
        :return: The response JSON from the Zenodo API
        :raises ValueError: if the response is missing a "bucket"
        """
        if isinstance(data, Metadata):
            data = {
                'metadata': {
                    key: value
                    for key, value in data.to_dict().items()
                    if value
                },
            }

        res = requests.post(
            self.depositions_base,
            json=data,
            params={'access_token': self.access_token},
        )
        res.raise_for_status()

        res_json = res.json()
        bucket = res_json.get('links', {}).get('bucket')
        if bucket is None:
            raise ValueError(f'No bucket in response. Got: {res_json}')

        self._upload_files(bucket=bucket, paths=paths)
        return self.publish(res_json['id'])

    def publish(self, deposition_id: str, sleep: bool = True) -> requests.Response:
        """Publish a record that's in edit mode.

        :param deposition_id: The identifier of the deposition on Zenodo. It should be in edit mode.
        :param sleep: Sleep for one second just in case of race conditions. If you're feeling lucky and rushed, you
            might be able to get away with disabling this.
        :return: The response JSON from the Zenodo API
        """
        if sleep:
            time.sleep(1)
        res = requests.post(
            f'{self.depositions_base}/{deposition_id}/actions/publish',
            params={'access_token': self.access_token},
        )
        res.raise_for_status()
        return res

    def update(self, deposition_id: str, paths: Union[str, Iterable[str]]) -> requests.Response:
        """Create a new version of the given record with the given files."""
        # Prepare a new version based on the old version
        # see: https://developers.zenodo.org/#new-version)
        res = requests.post(
            f'{self.depositions_base}/{deposition_id}/actions/newversion',
            params={'access_token': self.access_token},
        )
        res.raise_for_status()

        # Parse out the new version (@zenodo please give this as its own field!)
        new_deposition_id = res.json()['links']['latest_draft'].split('/')[-1]

        # Get all metadata associated with the new version (this has updated DOIs, etc.)
        # see: https://developers.zenodo.org/#retrieve
        res = requests.get(
            f'{self.depositions_base}/{new_deposition_id}',
            params={'access_token': self.access_token},
        )
        res.raise_for_status()
        new_deposition_data = res.json()
        # Update the version
        new_deposition_data['metadata']['version'] = _prepare_new_version(new_deposition_data['metadata']['version'])
        new_deposition_data['metadata']['publication_date'] = datetime.datetime.today().strftime('%Y-%m-%d')

        # Update the deposition for the new version
        # see: https://developers.zenodo.org/#update
        res = requests.put(
            f'{self.depositions_base}/{new_deposition_id}',
            json=new_deposition_data,
            params={'access_token': self.access_token},
        )
        res.raise_for_status()

        bucket = new_deposition_data['links']['bucket']

        # Upload new files. It calculates the hash on all of these, and if no files have changed,
        #  there will be no update
        self._upload_files(bucket=bucket, paths=paths)

        # Send the publish command
        return self.publish(new_deposition_id)

    def _upload_files(self, *, bucket: str, paths: Union[str, Iterable[str]]):
        if isinstance(paths, str):
            paths = [paths]
        # see https://developers.zenodo.org/#quickstart-upload
        for path in paths:
            with open(path, "rb") as file:
                res = requests.put(
                    f'{bucket}/{os.path.basename(path)}',
                    data=file,
                    params={'access_token': self.access_token},
                )
            res.raise_for_status()

    def get_record(self, record_id: Union[int, str]) -> requests.Response:
        """Get the metadata for a given record."""
        res = requests.get(
            f'{self.base}/records/{record_id}',
            params={'access_token': self.access_token},
        )
        res.raise_for_status()
        return res

    def get_latest_record(self, record_id: Union[int, str]) -> str:
        """Get the latest record related to the given record."""
        res_json = self.get_record(record_id).json()
        # Still works even in the case that the given record ID is the latest.
        latest = res_json['links']['latest'].split('/')[-1]
        logger.debug('latest for zenodo.record:%s is zenodo.record:%s', record_id, latest)
        return latest

    def download(self, record_id: Union[int, str], path: str, *, force: bool = False, parts: PartsHint = None) -> Path:
        """Download the file for the given record.

        :param record_id: The Zenodo record id
        :param path: The name of the file in the Zenodo record
        :param parts: Optional arguments on where to store with :func:`pystow.ensure`. If none given, goes in
            ``<PYSTOW_HOME>/zendoo/<CONCEPT_RECORD_ID>/<RECORD>/<PATH>``. Where ``CONCEPT_RECORD_ID`` is the
            consistent concept record ID for all versions of the same record. If a function is given, the function
            should take 3 position arguments: concept record id, record id, and version, then return a sequence for
            PyStow. The name of the file is automatically appended to the end of the sequence.
        :param force: Should the file be re-downloaded if it already is cached? Defaults to false.
        :returns: the path to the downloaded file.

        For example, to download the most recent version of NSoC-KG, you can
        use the following command:

        >>> path = Zenodo().download('4574555', 'triples.tsv')

        Even as new versions of the data are uploaded, this command will always
        be able to check if a new version is available, download it if it is, and
        return the local file path. If the most recent version is already downloaded,
        then it returns the local file path to the cached file.

        The file path uses :mod:`pystow` under the ``zenodo`` module and uses the
        "concept record ID" as a submodule since that is the consistent identifier
        between different records that are versions of the same data.
        """
        res_json = self.get_record(record_id).json()
        # conceptrecid is the consistent record ID for all versions of the same record
        concept_record_id = res_json['conceptrecid']
        version = res_json['metadata']['version']
        logger.debug('version for zenodo.record:%s is %s', record_id, version)

        for file in res_json['files']:
            if file['key'] == path:
                url = file['links']['self']
                break
        else:
            raise FileNotFoundError(f'zenodo.record:{record_id} does not have a file with key {path}')

        if parts is None:
            parts = ['zenodo', concept_record_id, version, path]
        elif callable(parts):
            parts = parts(concept_record_id, str(record_id), version)
        return pystow.ensure(*parts, url=url, force=force)

    def download_latest(
        self,
        record_id: Union[int, str],
        path: str,
        *,
        force: bool = False,
        parts: PartsHint = None,
    ) -> Path:
        """Download the latest version of the file."""
        latest_record_id = self.get_latest_record(record_id)
        return self.download(latest_record_id, path, force=force, parts=parts)


def _prepare_new_version(old_version: str) -> str:
    new_version = datetime.datetime.today().strftime('%Y-%m-%d')
    if old_version == new_version:
        new_version += '-1'
    elif old_version.startswith(new_version) and old_version[-2] == '-' and old_version[-1].isnumeric():
        new_version += '-' + str(1 + int(old_version[-1]))  # please don't do this more than 10 times a day
    return new_version
