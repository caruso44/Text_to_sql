import re

def extract_sql(code_block: str) -> str:
    pattern = r"```sql\s+(.*?)```"
    match = re.search(pattern, code_block, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None