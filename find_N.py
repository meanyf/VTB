# find_N.py
import re
import logging
from typing import Any, List, Tuple
from decimal import Decimal

import psycopg2.extras


MIN_CALLS = 100  # минимум вызовов
MAX_CANDIDATES = 50
MAX_ROWS_PER_CALL = 2.0
FAST_MEAN_MS = 30.0

# --- regex для поиска "точечных" выборок ---
CANDIDATE_PATTERNS = [
    re.compile(r"\bwhere\b[^;]*=\s*\$\d+", re.IGNORECASE),  # WHERE ... = $1
    re.compile(r"\bwhere\b[^;]*=\s*\d+", re.IGNORECASE),  # WHERE ... = 123
    re.compile(r"\blimit\s+1\b", re.IGNORECASE),
    re.compile(
        r"\bwhere\b[^;]*=\s*%\(\w+\)s", re.IGNORECASE
    ),  # SQLAlchemy named params
]


def is_n1_like(query_text: str) -> Tuple[bool, List[str]]:
    matched: List[str] = []
    text = query_text or ""
    for p in CANDIDATE_PATTERNS:
        if p.search(text):
            matched.append(p.pattern)
    return (len(matched) > 0, matched)


def detect_time_columns(cur) -> Tuple[str, str]:
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'pg_stat_statements'
          AND column_name IN ('total_exec_time','mean_exec_time','total_time','mean_time')
        """
    )
    cols = {row[0] for row in cur.fetchall()}

    if "total_exec_time" in cols and "mean_exec_time" in cols:
        return "total_exec_time", "mean_exec_time"
    if "total_time" in cols and "mean_time" in cols:
        return "total_time", "mean_time"

    raise RuntimeError("Не удалось определить колонки времени в pg_stat_statements")


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def fetch_stat_rows(conn) -> List[dict]:
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
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


def make_suggestion(query_text: str, rows_per_call: float) -> str:
    n1_like, _ = is_n1_like(query_text)
    if n1_like or rows_per_call <= MAX_ROWS_PER_CALL:
        return (
            "Подозрение на N+1: частые одиночные выборки.\n"
            "- В ORM: используйте eager loading (joinedload/selectinload; Django: select_related/prefetch_related).\n"
            "- Сгруппируйте: WHERE id IN (...), затем JOIN/AGG вместо множественных SELECT.\n"
            "- Для счётчиков: один запрос с LEFT JOIN + GROUP BY или оконные функции.\n"
            "- Рассмотрите кэширование часто запрашиваемых сущностей."
        )
    return "Высокое число вызовов — проверьте на предмет N+1 или горячей точки в коде."


def analyze_n_plus_one(conn):
    """Основная функция для запуска через меню (как run_explain, analyze_stats)."""
    logging.info("Finding N+1 candidates...")

    rows = fetch_stat_rows(conn)
    results: List[dict] = []
    for r in rows:
        qtext = (r.get("query") or "").strip()
        calls = int(r.get("calls") or 0)
        total_rows = _to_float(r.get("rows") or 0.0)
        mean_ms = _to_float(r.get("mean_time_ms") or 0.0)
        rows_per_call = (total_rows / calls) if calls else 0.0

        n1_like, matched = is_n1_like(qtext)

        score = 0
        if calls >= MIN_CALLS:
            score += 1
        if rows_per_call <= MAX_ROWS_PER_CALL:
            score += 1
        if n1_like:
            score += 2
        if mean_ms <= FAST_MEAN_MS and calls >= 100:
            score += 1

        if score >= 2:
            results.append(
                {
                    "calls": calls,
                    "rows_per_call": round(rows_per_call, 3),
                    "mean_ms": round(mean_ms, 3),
                    "queryid": r.get("queryid"),
                    "query_snippet": qtext.replace("\n", " ")[:300],
                    "matched": matched,
                    "suggestion": make_suggestion(qtext, rows_per_call),
                }
            )

    results = sorted(results, key=lambda x: (-x["calls"], x["rows_per_call"]))

    if not results:
        print(
            "Кандидаты не найдены.\n"
            "- Убедитесь, что pg_stat_statements.track = 'all'.\n"
            "- Выполните подозрительный код (например, DO-блок с 50 SELECT) для теста.\n"
            "- При необходимости увеличьте LIMIT или уменьшите MIN_CALLS."
        )
        return

    for i, c in enumerate(results[:MAX_CANDIDATES], 1):
        print(
            f"\n[{i}] calls={c['calls']} rows/call={c['rows_per_call']} mean_ms={c['mean_ms']}"
        )
        print("queryid:", c["queryid"])
        print("snippet:", c["query_snippet"])
        print("matched:", c["matched"])
        print("suggestion:\n", c["suggestion"])
