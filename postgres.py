import yaml
from sqlalchemy import create_engine, text

def run_sql(query: str):
    with open("config_secret.yaml", "r") as f:
        config = yaml.safe_load(f)
    db = config.get("DB_PARAMS")
    if not db:
        raise ValueError("DB_PARAMS not found in config.yaml")
    db_url = f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['dbname']}"
    engine = create_engine(db_url)
    output = []
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            output = [dict(row._mapping) for row in result]
    except Exception as e:
        print(f"Error executing SQL: {e}")
    return output

