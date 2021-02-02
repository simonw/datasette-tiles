from datasette import hookimpl
from datasette.utils.asgi import Response, NotFound
from datasette_tiles.utils import detect_mtiles_databases


@hookimpl
def register_routes():
    return [
        (r"/-/tiles$", index),
        (r"/-/tiles/(?P<db_name>[^/]+)$", explorer),
        (r"/-/tiles/(?P<db_name>[^/]+)/(?P<z>\d+)/(?P<x>\d+)/(?P<y>\d+)\.png$", tile),
    ]


async def index(datasette):
    return Response.html(
        await datasette.render_template(
            "mbtiles_index.html",
            {"mbtiles_databases": await detect_mtiles_databases(datasette)},
        )
    )


async def tile(request, datasette):
    db_name = request.url_vars["db_name"]
    mbtiles_databases = await detect_mtiles_databases(datasette)
    if db_name not in mbtiles_databases:
        raise NotFound("Not a valid mbtiles database")
    db = datasette.get_database(db_name)
    z = request.url_vars["z"]
    x = request.url_vars["x"]
    y = request.url_vars["y"]
    result = await db.execute(
        """
    select
      tile_data
    from
      tiles
    where 
      zoom_level = :z
      and tile_column = :x
      and tile_row = :y
    """,
        {
            "z": z,
            "x": x,
            "y": y,
        },
    )
    if not result.rows:
        raise NotFound("Tile not found")
    return Response(body=result.rows[0][0], content_type="image/png")


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
    return Response.html(
        await datasette.render_template(
            "mbtiles_explorer.html",
            {
                "metadata": metadata,
                "db_name": db_name,
                "default_latitude": default_latitude,
                "default_longitude": default_longitude,
                "default_zoom": default_zoom,
                "min_zoom": min_zoom,
                "max_zoom": max_zoom,
            },
        )
    )
