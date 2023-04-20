from string import Template

template = {
    "INSERT": Template("INSERT INTO $table $columns VALUES $values"),
    "DELETE": Template("DELETE FROM $table WHERE $filters"),
    "UPDATE": Template("UPDATE $table SET $update_field WHERE $filter")
}

def insert_placeholder(table: str, columns: list[str]):
    values_placeholder = [f':{n + 1}' for n, _ in enumerate(columns)]
    insert = template["INSERT"].safe_substitute(
        table=table,
        columns=f'({", ".join(columns)})',
        values=f'({", ".join(values_placeholder)})'
    )
    return insert