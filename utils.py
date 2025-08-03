import re
import yaml
import pandas as pd
from sqlalchemy import create_engine, text

from schemas.user import User


def extract_sql(code_block: str) -> str:
    """
    Extracts the SQL query string from a code block formatted as a Markdown SQL block.
    
    Args:
        code_block (str): A string containing a SQL code block formatted like ```sql ... ```.
    
    Returns:
        str: The extracted SQL query, or None if the pattern is not found.
    """
    pattern = r"```sql\s+(.*?)```"
    match = re.search(pattern, code_block, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def get_table_data(db_name: str, table_name: str):
    """
    Connects to a PostgreSQL database and retrieves up to 10,000 rows from a specified table.
    
    Args:
        db_name (str): Name of the target database.
        table_name (str): Name of the table to query.
    
    Returns:
        pd.DataFrame or dict: DataFrame with table data or dict containing an error message.
    """
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
    """
    Writes a single row of user data into a specified table in the PostgreSQL database.
    
    Args:
        db_name (str): Name of the target database.
        table_name (str): Name of the table where data will be inserted.
        data (User): A Pydantic model representing the user data to insert.
    
    Returns:
        dict: A status message indicating success or containing an error.
    """
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


def run_sql(query: str, db_name: str):
    """
    Executes a raw SQL query on a PostgreSQL database and returns the results.
    
    Args:
        query (str): The SQL query to execute.
        db_name (str): Name of the target database.
    
    Returns:
        list[dict]: A list of rows returned by the query, each as a dictionary.
    """
    with open("config_secret.yaml", "r") as f:
        config = yaml.safe_load(f)
    db = config.get("DB_LOGIN_PARAMS")
    if not db:
        raise ValueError("DB_PARAMS not found in config.yaml")
    db_url = f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db_name}"
    engine = create_engine(db_url)
    output = []
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            output = [dict(row._mapping) for row in result]
    except Exception as e:
        print(f"Error executing SQL: {e}")
    return output
