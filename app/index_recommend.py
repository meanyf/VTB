# index_recommend.py
import re


def recommend_indexes(sql_query: str):
    recommendations = []

    # Приводим запрос к нижнему регистру для унификации
    sql_query = sql_query.lower()

    # ---------- WHERE ----------
    where_conditions = re.findall(
        r"\bwhere\b(.*?)(\bgroup\b|\border\b|\blimit\b|$)", sql_query, re.DOTALL
    )
    if where_conditions:
        where_conditions = where_conditions[0][0]

        # Поддержка операторов >, <, =, like, between, in
        conditions = re.findall(
            r"(\w+\.\w+|\w+)\s*(>=?|<=?|=|like|between|in)\s*('[^']*'|\d+|\([^)]*\))",
            where_conditions,
        )
        for condition in conditions:
            field = condition[0]
            recommendations.append(
                f"Создать индекс на поле {field} для ускорения фильтрации."
            )

    # ---------- JOIN (ON) ----------
    join_conditions = re.findall(
        r"\bjoin\b\s+\w+(?:\s+\w+)?\s+on\s+([\w\.]+)\s*=\s*([\w\.]+)", sql_query
    )
    for left_field, right_field in join_conditions:
        recommendations.append(
            f"Создать индекс на поле {left_field} для ускорения соединений."
        )
        recommendations.append(
            f"Создать индекс на поле {right_field} для ускорения соединений."
        )

    # ---------- JOIN (USING) ----------
    join_using = re.findall(r"\bjoin\b\s+\w+(?:\s+\w+)?\s+using\s*\((\w+)\)", sql_query)
    for field in join_using:
        recommendations.append(
            f"Создать индекс на поле {field} для ускорения соединений."
        )

    # ---------- ORDER BY ----------
    order_by = re.search(r"\border\s+by\s+(.*)", sql_query)
    if order_by:
        order_fields = re.split(r",\s*", order_by.group(1))
        for field in order_fields:
            field = re.sub(r"\s+(asc|desc)\b", "", field).strip().rstrip(";")
            recommendations.append(
                f"Создать индекс на поле {field} для ускорения сортировки."
            )

    # Убираем дубли
    recommendations = list(set(recommendations))
    if not recommendations:
        recommendations.append("Индексы не требуются.")

    return recommendations


def analyze_indexes(query: str, conn=None):
    """Обёртка для вызова из меню (в стиле run_explain, analyze_stats)."""
    print("\nРекомендации по индексам:")
    try:
        # Проверяем корректность запроса через EXPLAIN
        with conn.cursor() as cur:
            cur.execute(f"EXPLAIN {query}")

        # Если EXPLAIN прошел успешно — вызываем рекомендации
        indexes = recommend_indexes(query)

        for idx in indexes:
            print("-", idx)
    except Exception as e:
        print(f"❌ Ошибка в SQL запросе: {e}")
        conn.rollback()

