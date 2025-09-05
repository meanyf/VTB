import re


def _remove_comments_and_literals(sql: str) -> str:
    # Remove single-line and multi-line comments
    sql = re.sub(r"--.*?$", " ", sql, flags=re.MULTILINE)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    # Replace string literals with empty quotes to avoid false positives inside them
    sql = re.sub(r"'(?:''|[^'])*'", "''", sql, flags=re.DOTALL)  # single quotes
    sql = re.sub(r'"(?:\\"|[^"])*"', '""', sql, flags=re.DOTALL)  # double quotes
    return sql


def _extract_between(sql: str, start_kw: str, stop_kws: list):
    # extract text starting after start_kw up to the nearest stop keyword or end
    pattern = (
        r"\b"
        + re.escape(start_kw)
        + r"\b(.*?)(?:\b(?:"
        + "|".join(map(re.escape, stop_kws))
        + r")\b|$)"
    )
    m = re.search(pattern, sql, flags=re.DOTALL)
    return m.group(1).strip() if m else ""


def analyze_sql(sql_query: str):
    original = sql_query
    sql = sql_query.lower()
    sql_clean = _remove_comments_and_literals(sql)
    recommendations = []

    # ---------- helper flags ----------
    has_select = bool(re.search(r"\bselect\b", sql_clean))
    has_limit = bool(re.search(r"\blimit\b", sql_clean))
    has_order_by = bool(re.search(r"\border\s+by\b", sql_clean))
    has_group_by = bool(re.search(r"\bgroup\s+by\b", sql_clean))
    has_having = bool(re.search(r"\bhaving\b", sql_clean))
    # count unions (word boundary)
    union_count = len(re.findall(r"\bunion\b", sql_clean))

    # ---------- 1. SELECT ----------
    if re.search(r"\bselect\s*\*\b", sql_clean):
        recommendations.append("❌ Используется SELECT * — выбирай только нужные поля.")

    if re.search(r"\bselect\b[\s\S]*?\(\s*select\b", sql_clean):
        recommendations.append(
            "⚠️ Подзапрос в SELECT — лучше переписать через JOIN/CTE."
        )

    # ---------- 2. LIMIT ----------
    if has_select and not has_limit:
        recommendations.append(
            "⚠️ Нет LIMIT — если не нужны все строки, лучше ограничить выборку."
        )

    # ---------- 3. WHERE ----------
    where_text = _extract_between(
        sql_clean,
        "where",
        ["group by", "order by", "limit", "offset", "having", "union"],
    )
    if where_text:
        if re.search(r"\b(date|lower|upper|cast)\s*\(", where_text):
            recommendations.append(
                "❌ В WHERE используется функция на поле — индекс не будет работать."
            )
        if re.search(r"\bor\b", where_text):
            recommendations.append(
                "⚠️ Используется OR в WHERE — может плохо работать с индексами; подумай о UNION/IN/EXISTS или выражениях по индексируемым полям."
            )
        if re.search(r"\bbetween\b", where_text):
            recommendations.append(
                "⚠️ Используется BETWEEN — иногда лучше заменить на >= и < для полуоткрытых интервалов."
            )
        if re.search(r"\b(?:like|ilike)\s*'%", where_text):
            recommendations.append(
                "⚠️ LIKE/ILIKE с ведущим % — индекс не будет использоваться; рассмотрите trigram/GIN или полнотекстовый поиск."
            )
        if re.search(r"\bin\s*\(\s*select\b", where_text):
            recommendations.append(
                "⚠️ Используется IN (subquery) — лучше заменить на EXISTS для большей эффективности при больших наборах."
            )

    # ---------- 4. JOIN ----------
    join_count = len(re.findall(r"\bjoin\b", sql_clean))
    if join_count > 0:
        if re.search(r"\bleft\s+join\b", sql_clean):
            recommendations.append(
                "⚠️ Используется LEFT JOIN — проверь, нужен ли именно он, а не INNER JOIN."
            )
        # Check each JOIN fragment for ON/USING
        join_positions = [m.start() for m in re.finditer(r"\bjoin\b", sql_clean)]
        for pos in join_positions:
            tail_match = re.search(
                r"\b(join|where|group by|order by|limit|offset|having|union)\b",
                sql_clean[pos + 4 :],
            )
            if tail_match:
                end_idx = pos + 4 + tail_match.start()
            else:
                end_idx = len(sql_clean)
            fragment = sql_clean[pos:end_idx]
            if " on " not in fragment and " using " not in fragment:
                recommendations.append(
                    "❌ JOIN без условия ON/USING — может вызвать декартово произведение."
                )
        if join_count > 4:
            recommendations.append(
                f"⚠️ Очень много JOIN ({join_count}) — стоит проверить необходимость и наличие индексов на полях соединения."
            )

    # ---------- 5. IN vs EXISTS (global fallback) ----------
    if re.search(r"\bin\s*\(\s*select\b", sql_clean) and "where" in sql_clean:
        recommendations.append(
            "⚠️ Используется IN (subquery) — для больших подзапросов EXISTS обычно эффективнее."
        )

    # ---------- 6. UNION ----------
    if re.search(r"\bunion\b(?!\s+all)", sql_clean):
        recommendations.append(
            "⚠️ Используется UNION — если дубликаты не нужны, лучше UNION ALL (быстрее)."
        )
    if union_count > 1:
        recommendations.append(
            "⚠️ Много UNION подряд — возможно, стоит использовать временные таблицы или CTE."
        )

    # ---------- 7. ORDER BY ----------
    if has_order_by and not has_limit:
        recommendations.append(
            "⚠️ ORDER BY без LIMIT — сортировка может быть очень тяжёлой; подумай о ограничении или индексах, покрывающих ORDER BY."
        )

    # ---------- 8. HAVING ----------
    if has_having and not has_group_by:
        recommendations.append(
            "❌ HAVING без GROUP BY — условие лучше перенести в WHERE."
        )

    # ---------- 9. COUNT(*) ----------
    if re.search(r"\bcount\s*\(\s*\*\s*\)\b", sql_clean) and "where" not in sql_clean:
        recommendations.append(
            "⚠️ COUNT(*) без WHERE — может быть очень тяжёлым на больших таблицах; возможно нужен материализованный подсчёт или индекс."
        )

    # ---------- 10. OFFSET ----------
    if re.search(r"\boffset\b", sql_clean):
        recommendations.append(
            "⚠️ Используется OFFSET — для больших смещений лучше keyset pagination (WHERE id > ?) или seek-pagination."
        )

    if not recommendations:
        return ["✅ Запрос выглядит нормально."]

    # Убираем дубликаты, сохраняя порядок
    seen = set()
    uniq = []
    for r in recommendations:
        if r not in seen:
            seen.add(r)
            uniq.append(r)
    return uniq
sql_query = """ SELECT DISTINCT (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) as cnt FROM users u LEFT JOIN departments d ON u.department_id = d.department_id JOIN logs l ON u.id = l.user_id WHERE DATE(u.created_at) = '2020-01-01' OR u.status = 'active' ORDER BY u.name OFFSET 10000; """
results = analyze_sql(sql_query)
for r in results:
    print(r)