from psycopg import rows
def print_plan_node(node, indent=0):
    prefix = "  " * indent
    print(f"{prefix}Node Type: {node.get('Node Type')}")
    if "Relation Name" in node:
        print(f"{prefix}Relation Name: {node['Relation Name']}")

    # Основные метрики
    actual_time = node.get("Actual Total Time", 0)
    print(
        f"{prefix}Plan Rows: {node.get('Plan Rows')}, Actual Rows: {node.get('Actual Rows')}"
    )
    print(
        f"{prefix}Total Cost: {node.get('Total Cost')}, Actual Total Time: {actual_time} ms"
    )
    print(f"{prefix}Loops: {node.get('Loops', 1)}")

    # Метрики буферов
    buffers_info = []
    for b in [
        "Shared Hit Blocks",
        "Shared Read Blocks",
        "Shared Dirtied Blocks",
        "Shared Written Blocks",
        "Local Hit Blocks",
        "Local Read Blocks",
        "Local Dirtied Blocks",
        "Local Written Blocks",
        "Temp Read Blocks",
        "Temp Written Blocks",
    ]:
        if b in node:
            buffers_info.append(f"{b}: {node[b]}")
    if buffers_info:
        print(f"{prefix}Buffers: {', '.join(buffers_info)}")

    # Для сортировки
    if node.get("Node Type") == "Sort":
        print(f"{prefix}Sort Method: {node.get('Sort Method')}")
        print(f"{prefix}Sort Space Used: {node.get('Sort Space Used', 0)}")

    # Время планирования
    if "Planning Time" in node:
        print(f"{prefix}Planning Time: {node['Planning Time']} ms")
    if "Execution Time" in node:
        print(f"{prefix}Execution Time: {node['Execution Time']} ms")

    if indent == 0:
        print(f"\n=== Суммарные метрики по всему плану ===")
        print(f"Total Actual Time: {actual_time} ms")

        buffer_fields = [
            "Shared Hit Blocks",
            "Shared Read Blocks",
            "Shared Dirtied Blocks",
            "Shared Written Blocks",
            "Local Hit Blocks",
            "Local Read Blocks",
            "Local Dirtied Blocks",
            "Local Written Blocks",
            "Temp Read Blocks",
            "Temp Written Blocks",
        ]
        total_buffers = sum(node.get(b, 0) for b in buffer_fields)
        print(f"Total Buffers: {total_buffers}")


def run_explain(query, conn, label="EXPLAIN"):
    print(f"\n=== {label} ===")
    cur = conn.cursor(row_factory=rows.dict_row)
    cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
    plan_raw = cur.fetchone()["QUERY PLAN"]
    top_plan = plan_raw[0]["Plan"]
    print_plan_node(top_plan)
    cur.close()
