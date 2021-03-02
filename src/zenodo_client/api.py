# -*- coding: utf-8 -*-

"""A client for Zenodo."""

import datetime
import logging
import os
import time
from typing import Any, Iterable, Mapping, Optional, Union

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
            self.base = 'https://sandbox.zenodo.org/api/deposit/depositions'
            self.token_key = 'sandbox_api_token'
        else:
            self.base = 'https://zenodo.org/api/deposit/depositions'
            self.token_key = 'api_token'

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
            self.base,
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
            f'{self.base}/{deposition_id}/actions/publish',
            params={'access_token': self.access_token},
        )
        res.raise_for_status()
        return res

    def update(self, deposition_id: str, paths: Union[str, Iterable[str]]) -> requests.Response:
        """Create a new version of the given record with the given files."""
        # Prepare a new version based on the old version
        # see: https://developers.zenodo.org/#new-version)
        res = requests.post(
            f'{self.base}/{deposition_id}/actions/newversion',
            params={'access_token': self.access_token},
        )
        res.raise_for_status()

        # Parse out the new version (@zenodo please give this as its own field!)
        new_deposition_id = res.json()['links']['latest_draft'].split('/')[-1]

        # Get all metadata associated with the new version (this has updated DOIs, etc.)
        # see: https://developers.zenodo.org/#retrieve
        res = requests.get(
            f'{self.base}/{new_deposition_id}',
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
            f'{self.base}/{new_deposition_id}',
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


def _prepare_new_version(old_version: str) -> str:
    new_version = datetime.datetime.today().strftime('%Y-%m-%d')
    if old_version == new_version:
        new_version += '-1'
    elif old_version.startswith(new_version) and old_version[-2] == '-' and old_version[-1].isnumeric():
        new_version += '-' + str(1 + int(old_version[-1]))  # please don't do this more than 10 times a day
    return new_version
