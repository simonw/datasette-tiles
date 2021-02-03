from setuptools import setup
import os

VERSION = "0.4"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="datasette-tiles",
    description="Mapping tile server for Datasette, serving tiles from MBTiles packages",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/simonw/datasette-tiles",
    project_urls={
        "Issues": "https://github.com/simonw/datasette-tiles/issues",
        "CI": "https://github.com/simonw/datasette-tiles/actions",
        "Changelpog": "https://github.com/simonw/datasette-tiles/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["datasette_tiles"],
    entry_points={"datasette": ["tiles = datasette_tiles"]},
    install_requires=["datasette", "datasette-leaflet>=0.2.2"],
    extras_require={"test": ["pytest", "pytest-asyncio", "datasette-basemap>=0.2"]},
    tests_require=["datasette-tiles[test]"],
    package_data={"datasette_tiles": ["templates/*"]},
    python_requires=">=3.6",
)
