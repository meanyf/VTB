def fetch_stat_rows(conn) -> List[dict]:
    with conn.cursor(row_factory=rows.dict_row) as cur:
        total_col, mean_col = detect_time_columns(cur)

        allowed = {"total_exec_time", "mean_exec_time", "total_time", "mean_time"}
        if total_col not in allowed or mean_col not in allowed:
            raise RuntimeError(f"Недопустимые колонки времени: {total_col}, {mean_col}")

        cur.execute(
            f"""
            SELECT
              queryid, dbid, userid, calls, rows,
              {total_col} AS total_time_ms,
              {mean_col}  AS mean_time_ms,
              query
            FROM pg_stat_statements
            WHERE calls >= %s
            ORDER BY calls DESC
            LIMIT %s
            """,
            (MIN_CALLS, MAX_CANDIDATES * 5),
        )
        return [dict(r) for r in cur.fetchall()]