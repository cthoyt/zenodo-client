<!--
<p align="center">
  <img src="docs/source/logo.png" height="150">
</p>
-->

<h1 align="center">
  Zenodo Client
</h1>

<p align="center">
    <a href="https://github.com/cthoyt/zenodo-client/actions?query=workflow%3ATests">
        <img alt="Tests" src="https://github.com/cthoyt/zenodo-client/workflows/Tests/badge.svg" />
    </a>
    <a href="https://github.com/cthoyt/cookiecutter-python-package">
        <img alt="Cookiecutter template from @cthoyt" src="https://img.shields.io/badge/Cookiecutter-python--package-yellow" /> 
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
    <a href="https://zenodo.org/badge/latestdoi/343513445">
        <img src="https://zenodo.org/badge/343513445.svg" alt="DOI">
    </a>
</p>

A wrapper for the Zenodo API.

## 💪 Getting Started

The first example shows how you can set some configuration then never worry about whether it's been
uploaded already or not - all baked in with PyStow. On the first time this script is run, the new
deposition is made, published, and the identifier is stored with the given key in your
`~/.config/zenodo.ini`. Next time it's run, the deposition will be looked up, and the data will be
uploaded. Versioning is given automatically by date, and if multiple versions are uploaded on one
day, then a dash and the revision are appended.

```python
from zenodo_client import Creator, Metadata, ensure_zenodo


def main():
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
        key='test3',
        data=data,
        paths='/Users/cthoyt/Desktop/test1.png',
        sandbox=True,
    )
    from pprint import pprint
    pprint(res.json())


if __name__ == '__main__':
    main()


```

The following example shows how to use the Zenodo uploader

```python
from zenodo_client import update_zenodo

# The ID from your deposition
SANDBOX_DEP_ID = '724868'

# Paths to local files. Good to use in combination with resources that are always
#  dumped to the same place by a given script
paths = [
   # os.path.join(DATABASE_DIRECTORY, 'alts_sample.tsv')
   '/Users/cthoyt/Desktop/alts_sample.tsv'
]

# Don't forget to set the ZENODO_API_TOKEN environment variable or
#  any valid way to get zenodo/api_token from PyStow.
update_zenodo(SANDBOX_DEP_ID, paths)
```

### Command Line Interface

The zenodo_client command line tool is automatically installed. It can
be used from the shell with the `--help` flag to show all subcommands:

```shell
$ zenodo_client --help
```

It can be run with `zenodo_client <deposition ID> <path 1> ... <path N>`

## ⬇️ Installation

The most recent release can be installed from
[PyPI](https://pypi.org/project/zenodo_client/) with:

```bash
$ pip install zenodo_client
```

The most recent code and data can be installed directly from GitHub with:

```bash
$ pip install git+https://github.com/cthoyt/zenodo-client.git
```

To install in development mode, use the following:

```bash
$ git clone git+https://github.com/cthoyt/zenodo-client.git
$ cd zenodo-client
$ pip install -e .
```

## ⚖️ License

The code in this package is licensed under the MIT License.

## 🙏 Contributing
Contributions, whether filing an issue, making a pull request, or forking, are appreciated. See
[CONTRIBUTING.rst](https://github.com/cthoyt/zenodo-client/blob/master/CONTRIBUTING.rst) for more information on getting
involved.

## 🍪 Cookiecutter Acknowledgement

This package was created with [@audreyr](https://github.com/audreyr)'s
[cookiecutter](https://github.com/cookiecutter/cookiecutter) package using [@cthoyt](https://github.com/cthoyt)'s
[cookiecutter-python-package](https://github.com/cthoyt/cookiecutter-python-package) template.

## 🛠️ Development

The final section of the README is for if you want to get involved by making a code contribution.

### ❓ Testing

After cloning the repository and installing `tox` with `pip install tox`, the unit tests in the `tests/` folder can be
run reproducibly with:

```shell
$ tox
```

Additionally, these tests are automatically re-run with each commit in a [GitHub Action](https://github.com/cthoyt/zenodo-client/actions?query=workflow%3ATests).

### 📦 Making a Release

After installing the package in development mode and installing
`tox` with `pip install tox`, the commands for making a new release are contained within the `finish` environment
in `tox.ini`. Run the following from the shell:

```shell
$ tox -e finish
```

This script does the following:

1. Uses BumpVersion to switch the version number in the `setup.cfg` and
   `src/zenodo_client/version.py` to not have the `-dev` suffix
2. Packages the code in both a tar archive and a wheel
3. Uploads to PyPI using `twine`. Be sure to have a `.pypirc` file configured to avoid the need for manual input at this
   step
4. Push to GitHub. You'll need to make a release going with the commit where the version was bumped.
5. Bump the version to the next patch. If you made big changes and want to bump the version by minor, you can
   use `tox -e bumpversion minor` after.
