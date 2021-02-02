# datasette-mbtiles

[![PyPI](https://img.shields.io/pypi/v/datasette-mbtiles.svg)](https://pypi.org/project/datasette-mbtiles/)
[![Changelog](https://img.shields.io/github/v/release/simonw/datasette-mbtiles?include_prereleases&label=changelog)](https://github.com/simonw/datasette-mbtiles/releases)
[![Tests](https://github.com/simonw/datasette-mbtiles/workflows/Test/badge.svg)](https://github.com/simonw/datasette-mbtiles/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/datasette-mbtiles/blob/main/LICENSE)

Datasette plugin for serving MBTiles map tiles

## Installation

Install this plugin in the same environment as Datasette.

    $ datasette install datasette-mbtiles

## Usage

Usage instructions go here.

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:

    cd datasette-mbtiles
    python3 -mvenv venv
    source venv/bin/activate

Or if you are using `pipenv`:

    pipenv shell

Now install the dependencies and tests:

    pip install -e '.[test]'

To run the tests:

    pytest
