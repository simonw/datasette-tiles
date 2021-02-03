from datasette import hookimpl
from datasette.utils.asgi import Response, NotFound
from datasette_tiles.utils import detect_mtiles_databases, tiles_stack_database_order
import json

# 256x256 PNG of colour #dddddd, compressed using https://squoosh.app
PNG_404 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00\x00\x00\x01\x00\x04\x00\x00"
    b"\x00\x00\xbc\xe9\x1a\xbb\x00\x00\x00\x9cIDATx\xda\xed\xce1\x01\x00\x00\x0c\x02"
    b"\xa0\xd9?\xe3\xba\x18\xc3\x07\x12\x90\xbf\xad\x08\x08\x08\x08\x08\x08\x08\x08"
    b"\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08"
    b"\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08"
    b"\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08"
    b"\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08"
    b"\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08"
    b"\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\x08\xac"
    b"\x03\x05\xddg\xde\x01\xd26\xe7\xdd\x00\x00\x00\x00IEND\xaeB`\x82"
)

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
        (r"/-/tiles-stack$", tiles_stack_explorer),
        (r"/-/tiles-stack/(?P<z>\d+)/(?P<x>\d+)/(?P<y>\d+)\.png$", tiles_stack),
    ]


async def index(datasette):
    return Response.html(
        await datasette.render_template(
            "tiles_index.html",
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
        return Response(body=PNG_404, content_type="image/png", status=404)
    return Response(body=tile, content_type="image/png")


async def tiles_stack(datasette, request):
    priority_order = await tiles_stack_database_order(datasette)
    # Try each database in turn
    for database in priority_order:
        tile = await load_tile(database, request)
        if tile is not None:
            return Response(body=tile, content_type="image/png")
    return Response(body=PNG_404, content_type="image/png", status=404)


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
            "tiles_explorer.html",
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


async def tiles_stack_explorer(datasette):
    attribution = ""
    # Find min/max zoom by looking at the stack
    priority_order = await tiles_stack_database_order(datasette)
    min_zooms = []
    max_zooms = []
    attributions = []
    for db in priority_order:
        metadata = {
            row["name"]: row["value"]
            for row in (await db.execute("select name, value from metadata")).rows
        }
        if "minzoom" in metadata:
            min_zooms.append(int(metadata["minzoom"]))
        if "maxzoom" in metadata:
            max_zooms.append(int(metadata["maxzoom"]))
    # If all attributions are the same, use that - otherwise leave blank
    if len(set(attributions)) == 1:
        attribution = attributions[0]
    min_zoom = min(min_zooms)
    max_zoom = max(max_zooms)
    return Response.html(
        await datasette.render_template(
            "tiles_stack_explorer.html",
            {
                "default_latitude": 0,
                "default_longitude": 0,
                "default_zoom": min_zoom,
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
