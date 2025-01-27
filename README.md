<!--
<p align="center">
  <img src="https://github.com/cthoyt/zenodo-client/raw/main/docs/source/logo.png" height="150">
</p>
-->

<h1 align="center">
  Zenodo Client
</h1>

<p align="center">
    <a href="https://github.com/cthoyt/zenodo-client/actions/workflows/tests.yml">
        <img alt="Tests" src="https://github.com/cthoyt/zenodo-client/actions/workflows/tests.yml/badge.svg" /></a>
    <a href="https://pypi.org/project/zenodo_client">
        <img alt="PyPI" src="https://img.shields.io/pypi/v/zenodo_client" /></a>
    <a href="https://pypi.org/project/zenodo_client">
        <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/zenodo_client" /></a>
    <a href="https://github.com/cthoyt/zenodo-client/blob/main/LICENSE">
        <img alt="PyPI - License" src="https://img.shields.io/pypi/l/zenodo_client" /></a>
    <a href='https://zenodo_client.readthedocs.io/en/latest/?badge=latest'>
        <img src='https://readthedocs.org/projects/zenodo_client/badge/?version=latest' alt='Documentation Status' /></a>
    <a href="https://codecov.io/gh/cthoyt/zenodo-client/branch/main">
        <img src="https://codecov.io/gh/cthoyt/zenodo-client/branch/main/graph/badge.svg" alt="Codecov status" /></a>  
    <a href="https://github.com/cthoyt/cookiecutter-python-package">
        <img alt="Cookiecutter template from @cthoyt" src="https://img.shields.io/badge/Cookiecutter-snekpack-blue" /></a>
    <a href="https://github.com/astral-sh/ruff">
        <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff" style="max-width:100%;"></a>
    <a href="https://github.com/cthoyt/zenodo-client/blob/main/.github/CODE_OF_CONDUCT.md">
        <img src="https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg" alt="Contributor Covenant"/></a>
    <a href="https://zenodo.org/badge/latestdoi/343513445">
        <img src="https://zenodo.org/badge/343513445.svg" alt="DOI"></a>
</p>

A wrapper for the Zenodo API

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

A real-world example can be found here: https://github.com/cthoyt/nsockg.

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

A real-world example can be found [here](https://github.com/pyobo/pyobo/blob/master/src/pyobo/resource_utils.py)
where the latest build of the [Ooh Na Na](https://cthoyt.com/2020/04/18/ooh-na-na.html) nomenclature
database is automatically downloaded from Zenodo, even though the PyOBO package only hardcodes the
first deposition ID.

### Command Line Interface

The zenodo_client command line tool is automatically installed.
It can be used from the console with the `--help` flag to show all subcommands:

```console
$ zenodo_client --help
```

It can be run with `zenodo_client <deposition ID> <path 1> ... <path N>`

## 🚀 Installation

The most recent release can be installed from
[PyPI](https://pypi.org/project/zenodo_client/) with uv:

```console
$ uv pip install zenodo_client
```

or with pip:

```console
$ python3 -m pip install zenodo_client
```

The most recent code and data can be installed directly from GitHub with uv:

```console
$ uv --preview pip install git+https://github.com/cthoyt/zenodo-client.git
```

or with pip:

```console
$ UV_PREVIEW=1 python3 -m pip install git+https://github.com/cthoyt/zenodo-client.git
```

Note that this requires setting `UV_PREVIEW` mode enabled until the uv build
backend becomes a stable feature.

## 👐 Contributing

Contributions, whether filing an issue, making a pull request, or forking, are
appreciated. See
[CONTRIBUTING.md](https://github.com/cthoyt/zenodo-client/blob/master/.github/CONTRIBUTING.md)
for more information on getting involved.

## 👋 Attribution

### ⚖️ License

The code in this package is licensed under the MIT License.

<!--
### 📖 Citation

Citation goes here!
-->

<!--
### 🎁 Support

This project has been supported by the following organizations (in alphabetical order):

- [Biopragmatics Lab](https://biopragmatics.github.io)

-->

<!--
### 💰 Funding

This project has been supported by the following grants:

| Funding Body  | Program                                                      | Grant Number |
|---------------|--------------------------------------------------------------|--------------|
| Funder        | [Grant Name (GRANT-ACRONYM)](https://example.com/grant-link) | ABCXYZ       |
-->

### 🍪 Cookiecutter

This package was created with
[@audreyfeldroy](https://github.com/audreyfeldroy)'s
[cookiecutter](https://github.com/cookiecutter/cookiecutter) package using
[@cthoyt](https://github.com/cthoyt)'s
[cookiecutter-snekpack](https://github.com/cthoyt/cookiecutter-snekpack)
template.

## 🛠️ For Developers

<details>
  <summary>See developer instructions</summary>

The final section of the README is for if you want to get involved by making a
code contribution.

### Development Installation

To install in development mode, use the following:

```console
$ git clone git+https://github.com/cthoyt/zenodo-client.git
$ cd zenodo-client
$ uv --preview pip install -e .
```

Alternatively, install using pip:

```console
$ UV_PREVIEW=1 python3 -m pip install -e .
```

Note that this requires setting `UV_PREVIEW` mode enabled until the uv build
backend becomes a stable feature.

### Updating Package Boilerplate

This project uses `cruft` to keep boilerplate (i.e., configuration, contribution
guidelines, documentation configuration) up-to-date with the upstream
cookiecutter package. Install cruft with either `uv tool install cruft` or
`python3 -m pip install cruft` then run:

```console
$ cruft update
```

More info on Cruft's update command is available
[here](https://github.com/cruft/cruft?tab=readme-ov-file#updating-a-project).

### 🥼 Testing

After cloning the repository and installing `tox` with
`uv tool install tox --with tox-uv` or
`python3 -m pip install tox tox-uv`, the unit tests in the `tests/` folder
can be run reproducibly with:

```console
$ tox -e py
```

Additionally, these tests are automatically re-run with each commit in a
[GitHub Action](https://github.com/cthoyt/zenodo-client/actions?query=workflow%3ATests).

### 📖 Building the Documentation

The documentation can be built locally using the following:

```console
$ git clone git+https://github.com/cthoyt/zenodo-client.git
$ cd zenodo-client
$ tox -e docs
$ open docs/build/html/index.html
```

The documentation automatically installs the package as well as the `docs` extra
specified in the [`pyproject.toml`](pyproject.toml). `sphinx` plugins like
`texext` can be added there. Additionally, they need to be added to the
`extensions` list in [`docs/source/conf.py`](docs/source/conf.py).

The documentation can be deployed to [ReadTheDocs](https://readthedocs.io) using
[this guide](https://docs.readthedocs.io/en/stable/intro/import-guide.html). The
[`.readthedocs.yml`](.readthedocs.yml) YAML file contains all the configuration
you'll need. You can also set up continuous integration on GitHub to check not
only that Sphinx can build the documentation in an isolated environment (i.e.,
with `tox -e docs-test`) but also that
[ReadTheDocs can build it too](https://docs.readthedocs.io/en/stable/pull-requests.html).

#### Configuring ReadTheDocs

1. Log in to ReadTheDocs with your GitHub account to install the integration at
   https://readthedocs.org/accounts/login/?next=/dashboard/
2. Import your project by navigating to https://readthedocs.org/dashboard/import
   then clicking the plus icon next to your repository
3. You can rename the repository on the next screen using a more stylized name
   (i.e., with spaces and capital letters)
4. Click next, and you're good to go!

### 📦 Making a Release

#### Configuring Zenodo

[Zenodo](https://zenodo.org) is a long-term archival system that assigns a DOI
to each release of your package.

1. Log in to Zenodo via GitHub with this link:
   https://zenodo.org/oauth/login/github/?next=%2F. This brings you to a page
   that lists all of your organizations and asks you to approve installing the
   Zenodo app on GitHub. Click "grant" next to any organizations you want to
   enable the integration for, then click the big green "approve" button. This
   step only needs to be done once.
2. Navigate to https://zenodo.org/account/settings/github/, which lists all of
   your GitHub repositories (both in your username and any organizations you
   enabled). Click the on/off toggle for any relevant repositories. When you
   make a new repository, you'll have to come back to this

After these steps, you're ready to go! After you make "release" on GitHub (steps
for this are below), you can navigate to
https://zenodo.org/account/settings/github/repository/cthoyt/zenodo-client
to see the DOI for the release and link to the Zenodo record for it.

#### Registering with the Python Package Index (PyPI)

You only have to do the following steps once.

1. Register for an account on the
   [Python Package Index (PyPI)](https://pypi.org/account/register)
2. Navigate to https://pypi.org/manage/account and make sure you have verified
   your email address. A verification email might not have been sent by default,
   so you might have to click the "options" dropdown next to your address to get
   to the "re-send verification email" button
3. 2-Factor authentication is required for PyPI since the end of 2023 (see this
   [blog post from PyPI](https://blog.pypi.org/posts/2023-05-25-securing-pypi-with-2fa/)).
   This means you have to first issue account recovery codes, then set up
   2-factor authentication
4. Issue an API token from https://pypi.org/manage/account/token

#### Configuring your machine's connection to PyPI

You have to do the following steps once per machine.

```console
$ uv tool install keyring
$ keyring set https://upload.pypi.org/legacy/ __token__
$ keyring set https://test.pypi.org/legacy/ __token__
```

Note that this deprecates previous workflows using `.pypirc`.

#### Uploading to PyPI

After installing the package in development mode and installing
`tox` with `uv tool install tox --with tox-uv` or
`python3 -m pip install tox tox-uv`, run the following from the console:

```console
$ tox -e finish
```

This script does the following:

1. Uses [bump-my-version](https://github.com/callowayproject/bump-my-version) to
   switch the version number in the `pyproject.toml`, `CITATION.cff`,
   `src/zenodo_client/version.py`, and
   [`docs/source/conf.py`](docs/source/conf.py) to not have the `-dev` suffix
2. Packages the code in both a tar archive and a wheel using
   [`uv build`](https://docs.astral.sh/uv/guides/publish/#building-your-package)
3. Uploads to PyPI using
   [`uv publish`](https://docs.astral.sh/uv/guides/publish/#publishing-your-package).
4. Push to GitHub. You'll need to make a release going with the commit where the
   version was bumped.
5. Bump the version to the next patch. If you made big changes and want to bump
   the version by minor, you can use `tox -e bumpversion -- minor` after.

#### Releasing on GitHub

1. Navigate to
   https://github.com/cthoyt/zenodo-client/releases/new
   to draft a new release
2. Click the "Choose a Tag" dropdown and select the tag corresponding to the
   release you just made
3. Click the "Generate Release Notes" button to get a quick outline of recent
   changes. Modify the title and description as you see fit
4. Click the big green "Publish Release" button

This will trigger Zenodo to assign a DOI to your release as well.

</details>
