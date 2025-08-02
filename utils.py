import re
import yaml

import pandas as pd
from sqlalchemy import create_engine, text

from schemas import User


def extract_sql(code_block: str) -> str:
    pattern = r"```sql\s+(.*?)```"
    match = re.search(pattern, code_block, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def get_table_data(db_name : str, table_name: str):
    with open("config_secret.yaml", "r") as f:
        config = yaml.safe_load(f)
    db = config.get("DB_LOGIN_PARAMS") 
    db_url = f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db_name}"
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            query = text(f'SELECT * FROM "{table_name}" LIMIT 10000')
            df = pd.read_sql(query, engine)
            return df
    except Exception as e:
        return {"error": str(e)}
    

def write_table_data(db_name: str, table_name: str, data: User):
    with open("config_secret.yaml", "r") as f:
        config = yaml.safe_load(f)
    db = config.get("DB_LOGIN_PARAMS")
    db_url = f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db_name}"
    try:
        engine = create_engine(db_url)
        df = pd.DataFrame([data.model_dump()])
        with engine.connect() as conn:
            df.to_sql(table_name, conn, if_exists='append', index=False)
        return {"status": "success", "rows_inserted": len(df)}
    except Exception as e:
        return {"error": str(e)}