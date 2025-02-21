Usage
=====

This example from PyOBO shows how to update a given deposition (the Zenodo word for a
record):

.. code-block::

    # The ID from your deposition
    SANDBOX_DEP_ID = '724868'

    # Don't forget to set the ZENODO_API_TOKEN environment variable or
    #  any valid way to get zenodo/api_token from PyStow.
    zenodo = Zenodo()

    # Paths to local files. Good to use in combination with resources that are always
    #  dumped to the same place by a given script
    paths = [
        # os.path.join(DATABASE_DIRECTORY, 'alts_sample.tsv')
        '/Users/cthoyt/Desktop/alts_sample.tsv'
    ]

    # Magically upload data to this record
    zenodo.update(SANDBOX_DEP_ID, paths)

Manually controlling publication of a record
--------------------------------------------

The following example creates a new deposit for a record and uses the pre-reserved DOI
before uploading files but does not publish the record, allowing manual editing in the
Zenodo UI.

.. code-block:: python

    from pathlib import Path
    from zenodo_client import (
        Creator,
        Metadata,
        create_zenodo,
        update_zenodo,
        publish_zenodo,
    )

    HERE = Path(__file__).parent.resolve()

    # Define the metadata that will be used on initial upload
    data = Metadata(
        title="Test Upload 3",
        upload_type="dataset",
        description="test description",
        creators=[
            Creator(
                name="Hoyt, Charles Tapley",
                orcid="0000-0003-4423-4370",
            ),
        ],
    )

    res = create_zenodo(data=data, sandbox=True, paths=[], publish=False)

    expected_doi = res.json()["metadata"]["prereserve_doi"]["doi"]

    path = HERE / "file.txt"
    path.write_text(
        expected_doi
    )  # this can be any text, we're just using the DOI as an example

    # Add files
    res = update_zenodo(deposition_id=res.json()["id"], paths=[path], publish=False)

    # Now check in Zenodo and publish there, or continue with
    res = publish_zenodo(deposition_id=res.json()["id"])
