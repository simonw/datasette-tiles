import asyncio
from datasette.app import Datasette
from datasette.database import Database
import pytest


CREATE_TILES_TABLE = "CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob)"
CREATE_METADATA_TABLE = "CREATE TABLE metadata (name text, value text)"


@pytest.fixture(scope="module")
async def ds():
    datasette = Datasette([], memory=True)
    await datasette.invoke_startup()
    return datasette


# Needed because of https://stackoverflow.com/a/56238383
# to allow me to use scope="module" on the ds() fixture below
@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def ds_tiles_stack():
    return await ds_tiles()


@pytest.fixture(scope="module")
async def ds_tiles_stack_with_stack_order():
    return await ds_tiles(
        {
            "plugins": {
                "datasette-tiles": {"tiles-stack-order": ["world", "country", "city2"]}
            }
        }
    )


async def ds_tiles(metadata=None):
    datasette = Datasette([], metadata=metadata or {}, memory=True)
    for db_name, tiles in (
        ("world", [[2, 1, 1]]),
        ("country", [[2, 2, 1], [2, 2, 2]]),
        ("city1", [[2, 2, 1]]),
        ("city2", [[2, 3, 3]]),
    ):
        db = datasette.add_database(Database(datasette, memory_name=db_name))
        # During test runs database tables may exist already
        if await db.table_exists("tiles"):
            continue
        await db.execute_write(CREATE_TILES_TABLE, block=True)
        await db.execute_write(CREATE_METADATA_TABLE, block=True)
        for pair in (("name", db_name), ("format", "png")):
            await db.execute_write(
                "insert into metadata (name, value) values (?, ?)",
                pair,
                block=True,
            )
        for tile in tiles:
            await db.execute_write(
                "insert into tiles (zoom_level, tile_column, tile_row, tile_data) values (?, ?, ?, ?)",
                tile + ["tms:{}:{}".format(db_name, "/".join(map(str, tile)))],
                block=True,
            )
    await datasette.invoke_startup()
    return datasette
