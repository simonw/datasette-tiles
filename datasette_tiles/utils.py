async def detect_mtiles_databases(datasette):
    await datasette.refresh_schemas()
    internal = datasette.get_database("_internal")
    result = await internal.execute(
        """
    select
      columns.database_name,
      columns.table_name,
      group_concat(columns.name) as columns
    from
      columns
    where
      columns.table_name = "tiles"
    group by
      columns.database_name,
      columns.table_name
    order by
      columns.table_name
    """
    )
    return [
        row["database_name"]
        for row in result.rows
        if set(row["columns"].split(",")).issuperset(
            {"tile_column", "tile_data", "tile_row", "zoom_level"}
        )
    ]


async def tiles_stack_database_order(datasette, request):
    mtiles_databases = await detect_mtiles_databases(datasette)
    database_names = [
        name for name in datasette.databases.keys() if name in mtiles_databases
    ]
    database_order = list(reversed(database_names))
    # if datasette-basemap is installed, move basemap to the end
    plugins = [
        p["name"] for p in (await datasette.client.get("/-/plugins.json")).json()
    ]
    if "datasette-basemap" in plugins and "basemap" in database_order:
        database_order.remove("basemap")
        database_order.append("basemap")
    return [datasette.databases[name] for name in database_order]
