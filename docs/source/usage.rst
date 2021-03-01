Usage
=====
This example from PyOBO shows how to update a given deposition (the Zenodo word for a record):

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
