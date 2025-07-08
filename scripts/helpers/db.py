import urllib.parse
from dotenv import dotenv_values
import sqlalchemy as sa
import pandas as pd

CONFIG = dotenv_values()

DB_CONFIG = {
    "host": CONFIG.get("DB_HOST", "localhost"),
    "port": CONFIG.get("DB_PORT", "5432"),
    "user": CONFIG.get("DB_USER", "postgres"),
    "password": urllib.parse.quote_plus(CONFIG.get("DB_PASSWORD", "postgres")),
    "dbname": CONFIG.get("DB_NAME", "postgres"),
}

DB_BAK_CONFIG = {
    "host": CONFIG.get("BAK_DB_HOST", "localhost"),
    "port": CONFIG.get("BAK_DB_PORT", "5432"),
    "user": CONFIG.get("BAK_DB_USER", "postgres"),
    "password": urllib.parse.quote_plus(CONFIG.get("BAK_DB_PASSWORD", "postgres")),
    "dbname": CONFIG.get("BAK_DB_NAME", "postgres"),
}

DB_ENGINE = sa.create_engine(
    f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
)

DB_BAK_ENGINE = sa.create_engine(
    f"postgresql+psycopg2://{DB_BAK_CONFIG['user']}:{DB_BAK_CONFIG['password']}@{DB_BAK_CONFIG['host']}:{DB_BAK_CONFIG['port']}/{DB_BAK_CONFIG['dbname']}"
)


def get_data(table_name, start_date, end_date):
    sql_query = f"""SELECT *
        FROM {table_name}
        WHERE TIMESTAMP BETWEEN '{start_date}' AND '{end_date}'"""
    return pd.read_sql(sql_query, DB_BAK_ENGINE)


def get_stn():
    sql_query = """SELECT id,name,station_type
        FROM observations_station
        ORDER BY id
        """
    return pd.read_sql(sql_query, DB_BAK_ENGINE)
