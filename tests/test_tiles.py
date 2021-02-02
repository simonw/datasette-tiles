from datasette.app import Datasette
from datasette.database import Database
from datasette_tiles.utils import detect_mtiles_databases
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path,expected_status_code",
    [
        ("/-/tiles/basemap/3/6/5.png", 200),
        ("/-/tiles/basemap/4/10/8.png", 200),
        ("/-/tiles/basemap/8/6/5.png", 404),
    ],
)
async def test_tile(path, expected_status_code):
    datasette = Datasette([], memory=True)
    await datasette.invoke_startup()
    response = await datasette.client.get(path)
    assert response.status_code == expected_status_code
    if expected_status_code == 200:
        assert response.headers["content-type"] == "image/png"


@pytest.mark.asyncio
async def test_tiles_index():
    datasette = Datasette([], memory=True)
    await datasette.invoke_startup()
    response = await datasette.client.get("/-/tiles")
    assert response.status_code == 200
    assert '<li><a href="/-/tiles/basemap">basemap</a></li>' in response.text


@pytest.mark.asyncio
async def test_tiles_explorer():
    datasette = Datasette([], memory=True)
    await datasette.invoke_startup()
    response = await datasette.client.get("/-/tiles/basemap")
    assert response.status_code == 200
    assert '"/-/tiles/basemap/{z}/{x}/{y}.png";' in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "i,create_table,should_be_mtiles",
    [
        (1, "", False),
        (2, "CREATE TABLE foo (id integer primary key)", False),
        (
            3,
            "CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob);",
            True,
        ),
        (
            4,
            "CREATE TABLE tiles (zoom_level integer, tile_row integer, tile_data blob);",
            False,
        ),
        (
            5,
            "CREATE TABLE tiles (id integer, zoom_level integer, tile_column integer, tile_row integer, tile_data blob);",
            True,
        ),
    ],
)
async def test_detect_mtiles_databases(i, create_table, should_be_mtiles):
    datasette = Datasette([])
    name = "db_{}".format(i)
    db = datasette.add_database(Database(datasette, memory_name=name))
    if create_table:
        await db.execute_write(create_table, block=True)
    result = await detect_mtiles_databases(datasette)
    expected = [name] if should_be_mtiles else []
    assert result == expected
