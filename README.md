<!--
<p align="center">
  <img src="docs/source/logo.png" height="150">
</p>
-->

<h1 align="center">
  Zenodo Client
</h1>

<p align="center">
    <a href="https://github.com/cthoyt/zenodo-client/actions/workflows/tests.yml">
        <img alt="Tests" src="https://github.com/cthoyt/zenodo-client/workflows/Tests/badge.svg" />
    </a>
    <a href="https://pypi.org/project/zenodo_client">
        <img alt="PyPI" src="https://img.shields.io/pypi/v/zenodo_client" />
    </a>
    <a href="https://pypi.org/project/zenodo_client">
        <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/zenodo_client" />
    </a>
    <a href="https://github.com/cthoyt/zenodo-client/blob/main/LICENSE">
        <img alt="PyPI - License" src="https://img.shields.io/pypi/l/zenodo_client" />
    </a>
    <a href='https://zenodo_client.readthedocs.io/en/latest/?badge=latest'>
        <img src='https://readthedocs.org/projects/zenodo_client/badge/?version=latest' alt='Documentation Status' />
    </a>
    <a href="https://codecov.io/gh/cthoyt/zenodo-client/branch/main">
        <img src="https://codecov.io/gh/cthoyt/zenodo-client/branch/main/graph/badge.svg" alt="Codecov status" />
    </a>  
    <a href="https://github.com/cthoyt/cookiecutter-python-package">
        <img alt="Cookiecutter template from @cthoyt" src="https://img.shields.io/badge/Cookiecutter-snekpack-blue" /> 
    </a>
    <a href='https://github.com/psf/black'>
        <img src='https://img.shields.io/badge/code%20style-black-000000.svg' alt='Code style: black' />
    </a>
    <a href="https://github.com/cthoyt/zenodo-client/blob/main/.github/CODE_OF_CONDUCT.md">
        <img src="https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg" alt="Contributor Covenant"/>
    </a>
    <a href="https://zenodo.org/badge/latestdoi/343513445">
        <img src="https://zenodo.org/badge/343513445.svg" alt="DOI">
    </a>
</p>

A wrapper for the Zenodo API.

## 💪 Getting Started

The first example shows how you can set some configuration then never worry about whether it's been
uploaded already or not - all baked in with [`pystow`](https://github.com/cthoyt/pystow). On the
first time this script is run, the new deposition is made, published, and the identifier is stored
with the given key in your `~/.config/zenodo.ini`. Next time it's run, the deposition will be looked
up, and the data will be uploaded. Versioning is given automatically by date, and if multiple
versions are uploaded on one day, then a dash and the revision are appended.

```python
from zenodo_client import Creator, Metadata, ensure_zenodo

# Define the metadata that will be used on initial upload
data = Metadata(
    title='Test Upload 3',
    upload_type='dataset',
    description='test description',
    creators=[
        Creator(
            name='Hoyt, Charles Tapley',
            affiliation='Harvard Medical School',
            orcid='0000-0003-4423-4370',
        ),
    ],
)
res = ensure_zenodo(
    key='test3',  # this is a unique key you pick that will be used to store
                  # the numeric deposition ID on your local system's cache
    data=data,
    paths=[
        '/Users/cthoyt/Desktop/test1.png',
    ],
    sandbox=True,  # remove this when you're ready to upload to real Zenodo
)
from pprint import pprint

pprint(res.json())
```

A real-world example can be found here: <https://github.com/cthoyt/nsockg>.

The following example shows how to use the Zenodo uploader if you already know what your deposition
identifier is.

```python
from zenodo_client import update_zenodo

# The ID from your deposition
SANDBOX_DEP_ID = '724868'

# Paths to local files. Good to use in combination with resources that are always
# dumped to the same place by a given script
paths = [
    # os.path.join(DATABASE_DIRECTORY, 'alts_sample.tsv')
    '/Users/cthoyt/Desktop/alts_sample.tsv',
]

# Don't forget to set the ZENODO_API_TOKEN environment variable or
# any valid way to get zenodo/api_token from PyStow.
update_zenodo(SANDBOX_DEP_ID, paths)
```

The following example shows how to look up the latest version of a record.

```python
from zenodo_client import Zenodo

zenodo = Zenodo()
OOH_NA_NA_RECORD = '4020486'
new_record = zenodo.get_latest_record(OOH_NA_NA_RECORD)
```

Even further, the latest version of `names.tsv.gz` can be automatically downloaded to the
`~/.data/zenodo/<conceptrecid>/<version>/<path>` via `pystow` with:

```python
from zenodo_client import Zenodo

zenodo = Zenodo()
OOH_NA_NA_RECORD = '4020486'
new_record = zenodo.download_latest(OOH_NA_NA_RECORD, 'names.tsv.gz')
```

The following example creates a new deposit for a record and uses the prereserved DOI before uploading files but does not publish the record, allowing manual editing in the Zenodo UI.

```python
from zenodo_client import Creator, Metadata, create_zenodo, upload_zenodo

# Define the metadata that will be used on initial upload
data = Metadata(
    title='Test Upload 3',
    upload_type='dataset',
    description='test description',
    creators=[
        Creator(
            name='Hoyt, Charles Tapley',
            affiliation='Harvard Medical School',
            orcid='0000-0003-4423-4370',
        ),
    ],
)

res = create_zenodo(
    data=data,
    sandbox=True,
    paths=[],
    publish=False
)

from pprint import pprint
pprint(res.json())

# Create a file using the expected DOI
with open('file.txt', 'w') as file:  
    file.writelines(res.json()["metadata"]["prereserve_doi"]["doi"])

paths = [
    os.path.join(os.getcwd(), 'file.txt),
]

# Add files
res = update_zenodo(deposition_id=res["deposition_id"], paths=paths)
pprint(res.json())

# Update metadata (can also be combined with publish)
data.description='corrected test description'
res = update_metadata_zenodo(deposition_id=res["deposition_id"], data=data)
pprint(res.json())

res = publish_zenodo(deposition_id=res["deposition_id"])
pprint(res.json())
```

A real-world example can be found [here](https://github.com/pyobo/pyobo/blob/master/src/pyobo/resource_utils.py)
where the latest build of the [Ooh Na Na](https://cthoyt.com/2020/04/18/ooh-na-na.html) nomenclature
database is automatically downloaded from Zenodo, even though the PyOBO package only hardcodes the
first deposition ID.

### Command Line Interface

The zenodo_client command line tool is automatically installed. It can be used from the shell with
the `--help` flag to show all subcommands:

```shell
$ zenodo_client --help
```

It can be run with `zenodo_client <deposition ID> <path 1> ... <path N>`

## 🚀 Installation

The most recent release can be installed from
[PyPI](https://pypi.org/project/zenodo_client/) with:

```shell
$ pip install zenodo_client
```

The most recent code and data can be installed directly from GitHub with:

```bash
$ pip install git+https://github.com/cthoyt/zenodo-client.git
```

## 👐 Contributing

Contributions, whether filing an issue, making a pull request, or forking, are appreciated. See
[CONTRIBUTING.md](https://github.com/cthoyt/zenodo-client/blob/master/.github/CONTRIBUTING.md) for more information on getting involved.

## 👋 Attribution

### ⚖️ License

The code in this package is licensed under the MIT License.

### 🍪 Cookiecutter

This package was created with [@audreyfeldroy](https://github.com/audreyfeldroy)'s
[cookiecutter](https://github.com/cookiecutter/cookiecutter) package using [@cthoyt](https://github.com/cthoyt)'s
[cookiecutter-snekpack](https://github.com/cthoyt/cookiecutter-snekpack) template.

## 🛠️ For Developers

<details>
  <summary>See developer instructions</summary>

The final section of the README is for if you want to get involved by making a code contribution.

### Development Installation

To install in development mode, use the following:

```bash
$ git clone git+https://github.com/cthoyt/zenodo-client.git
$ cd zenodo-client
$ pip install -e .
```

### 🥼 Testing

After cloning the repository and installing `tox` with `pip install tox`, the unit tests in the `tests/` folder can be
run reproducibly with:

```shell
$ tox
```

Additionally, these tests are automatically re-run with each commit in a [GitHub Action](https://github.com/cthoyt/zenodo-client/actions?query=workflow%3ATests).

### 📖 Building the Documentation

The documentation can be built locally using the following:

```shell
$ git clone git+https://github.com/cthoyt/zenodo-client.git
$ cd zenodo-client
$ tox -e docs
$ open docs/build/html/index.html
``` 

The documentation automatically installs the package as well as the `docs`
extra specified in the [`setup.cfg`](setup.cfg). `sphinx` plugins
like `texext` can be added there. Additionally, they need to be added to the
`extensions` list in [`docs/source/conf.py`](docs/source/conf.py).

### 📦 Making a Release

After installing the package in development mode and installing
`tox` with `pip install tox`, the commands for making a new release are contained within the `finish` environment
in `tox.ini`. Run the following from the shell:

```shell
$ tox -e finish
```

This script does the following:

1. Uses [Bump2Version](https://github.com/c4urself/bump2version) to switch the version number in the `setup.cfg`,
   `src/zenodo_client/version.py`, and [`docs/source/conf.py`](docs/source/conf.py) to not have the `-dev` suffix
2. Packages the code in both a tar archive and a wheel using [`build`](https://github.com/pypa/build)
3. Uploads to PyPI using [`twine`](https://github.com/pypa/twine). Be sure to have a `.pypirc` file configured to avoid the need for manual input at this
   step
4. Push to GitHub. You'll need to make a release going with the commit where the version was bumped.
5. Bump the version to the next patch. If you made big changes and want to bump the version by minor, you can
   use `tox -e bumpversion -- minor` after.
</details>
