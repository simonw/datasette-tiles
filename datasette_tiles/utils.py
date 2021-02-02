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
