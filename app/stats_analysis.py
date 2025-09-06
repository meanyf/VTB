from psycopg import rows
import json


def detect_query_type(query: str) -> str:
    q = query.strip().upper()
    if q.startswith("SELECT"):
        return "SELECT"
    elif q.startswith("INSERT"):
        return "INSERT"
    elif q.startswith("UPDATE"):
        return "UPDATE"
    elif q.startswith("DELETE"):
        return "DELETE"
    return "OTHER"


def aggregate_query_stats(stats):
    agg = {}
    for row in stats:
        qtype = detect_query_type(row["query"])
        if qtype not in agg:
            agg[qtype] = {"calls": 0, "rows": 0, "total_time": 0.0}
        agg[qtype]["calls"] += row["calls"]
        agg[qtype]["rows"] += row["rows"]
        agg[qtype]["total_time"] += row["mean_exec_time"] * row["calls"]

    for qtype, values in agg.items():
        if values["calls"] > 0:
            values["avg_exec_time"] = values["total_time"] / values["calls"]
        else:
            values["avg_exec_time"] = 0.0
        del values["total_time"]
    return agg


def generate_autovacuum_recommendations(agg):
    recs = []
    total_calls = sum(v["calls"] for v in agg.values()) or 1

    # 1. много UPDATE/DELETE → уменьшить vacuum_scale_factor
    upd_del_calls = agg.get("UPDATE", {}).get("calls", 0) + agg.get("DELETE", {}).get(
        "calls", 0
    )
    upd_del_ratio = upd_del_calls / total_calls
    if upd_del_ratio > 0.2:
        recs.append(
            "Обнаружено много UPDATE/DELETE — рекомендуется снизить "
            "autovacuum_vacuum_scale_factor до 0.01–0.05 для горячих таблиц."
        )

    # 2. много INSERT → уменьшить analyze_scale_factor
    insert_ratio = agg.get("INSERT", {}).get("calls", 0) / total_calls
    if insert_ratio > 0.2:
        recs.append(
            "Обнаружено много INSERT — рекомендуется снизить autovacuum_analyze_scale_factor "
            "до 0.05 для поддержания актуальной статистики."
        )

    # 3. SELECT медленные → возможно bloat
    if "SELECT" in agg and agg["SELECT"]["avg_exec_time"] > 10:
        recs.append(
            f"Среднее время SELECT={agg['SELECT']['avg_exec_time']:.2f} мс — возможно, "
            "таблицы раздулись (bloat). Рекомендуется чаще запускать autovacuum."
        )

    if not recs:
        recs.append("Autovacuum работает нормально, критичных проблем не обнаружено.")

    return recs


def analyze_stats(query, conn):
    # Выполним запрос, чтобы получить статистику
    cur = conn.cursor(row_factory=rows.dict_row)

    # Получаем статистику по данному запросу, если это SELECT, INSERT, UPDATE или DELETE
    cur.execute(
        """
        SELECT query, calls, rows, mean_exec_time
        FROM pg_stat_statements
        WHERE query LIKE %s
        ORDER BY calls DESC
        LIMIT 100;
        """,
        ("%" + query + "%",),
    )

    stats = cur.fetchall()

    agg = aggregate_query_stats(stats)
    recs = generate_autovacuum_recommendations(agg)

    result = {"query_summary": agg, "recommendations": recs}

    print(json.dumps(result, indent=4, ensure_ascii=False))

    cur.close()
