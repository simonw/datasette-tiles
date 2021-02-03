from datasette import hookimpl
from datasette.utils.asgi import Response, NotFound
from datasette_tiles.utils import detect_mtiles_databases, tiles_stack_database_order
import json

SELECT_TILE_SQL = """
select
  tile_data
from
  tiles
where
  zoom_level = :z
  and tile_column = :x
  and tile_row = :y
""".strip()


@hookimpl
def register_routes():
    return [
        (r"/-/tiles$", index),
        (r"/-/tiles/(?P<db_name>[^/]+)$", explorer),
        (r"/-/tiles/(?P<db_name>[^/]+)/(?P<z>\d+)/(?P<x>\d+)/(?P<y>\d+)\.png$", tile),
        (r"/-/tiles-stack/(?P<z>\d+)/(?P<x>\d+)/(?P<y>\d+)\.png$", tiles_stack),
    ]


async def index(datasette):
    return Response.html(
        await datasette.render_template(
            "mbtiles_index.html",
            {"mbtiles_databases": await detect_mtiles_databases(datasette)},
        )
    )


async def load_tile(db, request):
    z = request.url_vars["z"]
    x = request.url_vars["x"]
    y = request.url_vars["y"]
    result = await db.execute(
        SELECT_TILE_SQL,
        {
            "z": z,
            "x": x,
            "y": y,
        },
    )
    if not result.rows:
        return None
    return result.rows[0][0]


async def tile(request, datasette):
    db_name = request.url_vars["db_name"]
    mbtiles_databases = await detect_mtiles_databases(datasette)
    if db_name not in mbtiles_databases:
        raise NotFound("Not a valid mbtiles database")
    db = datasette.get_database(db_name)
    tile = await load_tile(db, request)
    if tile is None:
        raise NotFound("Tile not found")
    return Response(body=tile, content_type="image/png")


async def tiles_stack(datasette, request):
    priority_order = await tiles_stack_database_order(datasette)
    # Try each database in turn
    for database in priority_order:
        tile = await load_tile(database, request)
        if tile is not None:
            return Response(body=tile, content_type="image/png")
    raise NotFound("Tile not found")


async def explorer(datasette, request):
    db_name = request.url_vars["db_name"]
    mbtiles_databases = await detect_mtiles_databases(datasette)
    if db_name not in mbtiles_databases:
        raise NotFound("Not a valid mbtiles database")
    db = datasette.get_database(db_name)
    metadata = {
        row["name"]: row["value"]
        for row in (await db.execute("select name, value from metadata")).rows
    }
    default_latitude = 0
    default_longitude = 0
    default_zoom = 0
    if metadata.get("center") and len(metadata["center"].split(",")) == 3:
        default_longitude, default_latitude, default_zoom = metadata["center"].split(
            ","
        )
    min_zoom = 0
    max_zoom = 19
    if metadata.get("minzoom"):
        min_zoom = metadata["minzoom"]
    if metadata.get("maxzoom"):
        max_zoom = metadata["maxzoom"]
    attribution = metadata.get("attribution") or None
    return Response.html(
        await datasette.render_template(
            "mbtiles_explorer.html",
            {
                "metadata": metadata,
                "db_name": db_name,
                "db_path": datasette.urls.database(db_name),
                "default_latitude": default_latitude,
                "default_longitude": default_longitude,
                "default_zoom": default_zoom,
                "min_zoom": min_zoom,
                "max_zoom": max_zoom,
                "attribution": json.dumps(attribution),
            },
        )
    )


@hookimpl
def database_actions(datasette, database):
    async def inner():
        mbtiles_databases = await detect_mtiles_databases(datasette)
        if database in mbtiles_databases:
            return [
                {
                    "href": datasette.urls.path("/-/tiles/{}".format(database)),
                    "label": "Explore these tiles on a map",
                }
            ]

    return inner


@hookimpl
def table_actions(datasette, database, table):
    async def inner():
        if table != "tiles":
            return None
        mbtiles_databases = await detect_mtiles_databases(datasette)
        if database in mbtiles_databases:
            return [
                {
                    "href": datasette.urls.path("/-/tiles/{}".format(database)),
                    "label": "Explore these tiles on a map",
                }
            ]

    return inner
