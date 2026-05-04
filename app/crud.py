from app import database


def _where(filters: dict, start: int = 1):
    keys = list(filters.keys())
    clause = " AND ".join(f"{k} = ${start + i}" for i, k in enumerate(keys))
    return clause, list(filters.values())


def _build_select(
    table: str,
    filters: dict = {},
    order_by: str = None,
    group_by: str = None,
    having: dict = {},
    limit: int = None,
    offset: int = None,
):
    vals = []
    i = 1
    q = f"SELECT * FROM {table}"

    if filters:
        clause, fvals = _where(filters, i)
        q += f" WHERE {clause}"
        vals += fvals
        i += len(fvals)

    if group_by:
        q += f" GROUP BY {group_by}"

    if having:
        clause, hvals = _where(having, i)
        q += f" HAVING {clause}"
        vals += hvals
        i += len(hvals)

    if order_by:
        q += f" ORDER BY {order_by}"

    if limit is not None:
        q += f" LIMIT ${i}"
        vals.append(limit)
        i += 1

    if offset is not None:
        q += f" OFFSET ${i}"
        vals.append(offset)
        i += 1

    return q, vals


async def fetch_one(
    table: str,
    filters: dict = {},
    order_by: str = None,
):
    q, vals = _build_select(table, filters, order_by=order_by, limit=1)
    return await database.pool.fetchrow(q, *vals)


async def fetch_all(
    table: str,
    filters: dict = {},
    order_by: str = None,
    group_by: str = None,
    having: dict = {},
    limit: int = None,
    offset: int = None,
):
    q, vals = _build_select(table, filters, order_by, group_by, having, limit, offset)
    return await database.pool.fetch(q, *vals)


async def insert(table: str, data: dict):
    keys = list(data.keys())
    cols = ", ".join(keys)
    vals = ", ".join(f"${i+1}" for i in range(len(keys)))
    return await database.pool.fetchrow(
        f"INSERT INTO {table} ({cols}) VALUES ({vals}) RETURNING *",
        *data.values()
    )


async def insert_many(table: str, rows: list[dict]):
    if not rows:
        return
    keys = list(rows[0].keys())
    cols = ", ".join(keys)
    all_vals = []
    placeholders = []
    i = 1
    for row in rows:
        ph = ", ".join(f"${i+j}" for j in range(len(keys)))
        placeholders.append(f"({ph})")
        all_vals += list(row.values())
        i += len(keys)
    q = f"INSERT INTO {table} ({cols}) VALUES {', '.join(placeholders)} RETURNING *"
    return await database.fetch(q, *all_vals)


async def update(table: str, data: dict, filters: dict):
    data_keys = list(data.keys())
    i = 1
    set_clause = ", ".join(f"{k} = ${i+j}" for j, k in enumerate(data_keys))
    i += len(data_keys)
    filter_clause, fvals = _where(filters, i)
    q = f"UPDATE {table} SET {set_clause} WHERE {filter_clause} RETURNING *"
    return await database.pool.fetchrow(q, *data.values(), *fvals)


async def update_many(table: str, data: dict, filters: dict):
    data_keys = list(data.keys())
    i = 1
    set_clause = ", ".join(f"{k} = ${i+j}" for j, k in enumerate(data_keys))
    i += len(data_keys)
    filter_clause, fvals = _where(filters, i)
    q = f"UPDATE {table} SET {set_clause} WHERE {filter_clause} RETURNING *"
    return await database.pool.fetch(q, *data.values(), *fvals)


async def delete(table: str, filters: dict):
    clause, vals = _where(filters)
    await database.pool.execute(
        f"DELETE FROM {table} WHERE {clause}", *vals
    )


async def delete_many(table: str, filters: dict):
    clause, vals = _where(filters)
    return await database.pool.fetch(
        f"DELETE FROM {table} WHERE {clause} RETURNING *", *vals
    )


async def exists(table: str, filters: dict) -> bool:
    clause, vals = _where(filters)
    row = await database.pool.fetchrow(
        f"SELECT 1 FROM {table} WHERE {clause} LIMIT 1", *vals
    )
    return row is not None


async def count(table: str, filters: dict = {}) -> int:
    q = f"SELECT COUNT(*) FROM {table}"
    vals = []
    if filters:
        clause, vals = _where(filters)
        q += f" WHERE {clause}"
    row = await database.pool.fetchrow(q, *vals)
    return row["count"]