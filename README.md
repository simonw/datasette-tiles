# datasette-tiles

[![PyPI](https://img.shields.io/pypi/v/datasette-tiles.svg)](https://pypi.org/project/datasette-tiles/)
[![Changelog](https://img.shields.io/github/v/release/simonw/datasette-tiles?include_prereleases&label=changelog)](https://github.com/simonw/datasette-tiles/releases)
[![Tests](https://github.com/simonw/datasette-tiles/workflows/Test/badge.svg)](https://github.com/simonw/datasette-tiles/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/datasette-tiles/blob/main/LICENSE)

Datasette plugin for serving MBTiles map tiles

## Installation

Install this plugin in the same environment as Datasette.

    $ datasette install datasette-tiles

## Demo

You can try this plugin out at https://datasette-tiles-demo.datasette.io/-/tiles

## Usage

This plugin scans all database files connected to Datasette to see if any of them are valid MBTiles databases.

It can then serve tiles from those databases at the following URL:

    /-/tiles/db-name/zoom/x/y.png

An example map for each database demonstrating the configured minimum and maximum zoom for that database can be found at `/-/tiles/db-name` - this can also be accessed via the table and database action menus for that database.

Visit `/-/tiles` for an index page of attached valid databases.

You can install the [datasette-basemap](https://datasette.io/plugins/datasette-basemap) plugin to get a `basemap` default set of tiles, handling zoom levels 0 to 6 using OpenStreetMap.

### Tile stacks

`datasette-tiles` can be configured to serve tiles from multiple attached MBTiles files, searching each database in order for a tile and falling back to the next in line if that tile is not found.

For a demo of this in action, visit https://datasette-tiles-demo.datasette.io/-/tiles-stack and zoom in on Japan. It should start showing [Stamen's Toner map](maps.stamen.com) of Japan once you get to zoom level 6 and 7.

The `/-/tiles-stack/1/1/1.png` endpoint provides this feature.

If you start Datasette like this:

    datasette world.mbtiles country.mbtiles city1.mbtiles city2.mbtiles

Any requests for a tile from the `/-/tiles-stack` path will first check the `city2` database, than `city1`, then `country`, then `world`.

If you have the [datasette-basemap](https://datasette.io/plugins/datasette-basemap) plugin installed it will be given special treatment: the `basemap` database will always be the last database checked for a tile.

Rather than rely on the order in which databases were attached, you can instead configure an explicit order using the `tiles-stack-order` plugin setting. Add the following to your `metadata.json` file:

```json
{
    "plugins": {
        "datasette-tiles": {
            "tiles-stack-order": ["world", "country"]
        }
    }
}
```

You can then run Datasette like this:

    datasette -m metadata.json country.mbtiles world.mbtiles

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:

    cd datasette-tiles
    python3 -mvenv venv
    source venv/bin/activate

Or if you are using `pipenv`:

    pipenv shell

Now install the dependencies and tests:

    pip install -e '.[test]'

To run the tests:

    pytest
