import pytest


@pytest.mark.asyncio
async def test_ds_tiles_stack_order(ds_tiles_stack):
    names = list(ds_tiles_stack.databases.keys())
    assert names[0] in (":memory:", "_memory")
    # basemap comes last because it was added by the datasette-basemap plugin
    assert names[1:] == ["_internal", "world", "country", "city1", "city2", "basemap"]
    # Confirm that datasette-basemap plugin is installed
    plugins = (await ds_tiles_stack.client.get("/-/plugins.json")).json()
    assert "datasette-basemap" in {p["name"] for p in plugins}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path,expected_tile",
    [
        # expected_tile=PNG means the tile should be a PNG from basemap
        # datasette-tiles gives "basemap" special treatment if datasette-basemap
        # is installed
        ("/-/tiles-stack/3/3/3.png", "PNG"),
        ("/-/tiles-stack/1/1/1.png", "world:1/1/1"),
        ("/-/tiles-stack/1/1/2.png", "country:1/1/2"),
        ("/-/tiles-stack/1/3/3.png", "city2:1/3/3"),
        # This tile is present in both country and city1:
        ("/-/tiles-stack/1/2/2.png", "city1:1/2/2"),
    ],
)
async def test_ds_tiles_stack(ds_tiles_stack, path, expected_tile):
    response = await ds_tiles_stack.client.get(path)
    if expected_tile == "PNG":
        assert response.content[:4] == b"\x89PNG"
    else:
        assert response.text == expected_tile
