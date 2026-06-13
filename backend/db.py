from __future__ import annotations

import os
import re
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:  # pragma: no cover - depends on local environment
    mysql = None
    MySQLError = Exception


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS fact_check_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    source_name VARCHAR(160) NOT NULL,
    source_region VARCHAR(40) NOT NULL,
    source_reliability INT NOT NULL,
    title VARCHAR(700) NOT NULL,
    summary TEXT NULL,
    url VARCHAR(1200) NOT NULL,
    published_at VARCHAR(80) NULL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags VARCHAR(500) NULL,
    UNIQUE KEY uniq_source_url (source_name, url(700)),
    INDEX idx_source_region (source_region),
    INDEX idx_title (title(255))
);
"""


def get_database_config() -> DatabaseConfig:
    return DatabaseConfig(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "debatetrix"),
    )


def is_mysql_driver_available() -> bool:
    return mysql is not None


@contextmanager
def mysql_connection(config: DatabaseConfig | None = None, with_database: bool = True) -> Iterator[object]:
    if mysql is None:
        raise RuntimeError("mysql-connector-python is not installed. Run: pip install -r requirements.txt")
    config = config or get_database_config()
    kwargs = {
        "host": config.host,
        "port": config.port,
        "user": config.user,
        "password": config.password,
        "autocommit": True,
    }
    if with_database:
        kwargs["database"] = config.database
    connection = mysql.connector.connect(**kwargs)
    try:
        yield connection
    finally:
        connection.close()


def initialize_database(config: DatabaseConfig | None = None) -> tuple[bool, str]:
    config = config or get_database_config()
    try:
        with mysql_connection(config, with_database=False) as connection:
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{config.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.close()
        with mysql_connection(config, with_database=True) as connection:
            cursor = connection.cursor()
            cursor.execute(SCHEMA_SQL)
            cursor.close()
        return True, f"MySQL ready: {config.user}@{config.host}:{config.port}/{config.database}"
    except Exception as exc:
        return False, str(exc)


def save_fact_items(items: list[dict[str, object]], config: DatabaseConfig | None = None) -> tuple[int, str]:
    if not items:
        return 0, "No new items fetched."
    ok, message = initialize_database(config)
    if not ok:
        return 0, message
    query = """
        INSERT IGNORE INTO fact_check_items
        (source_name, source_region, source_reliability, title, summary, url, published_at, tags)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = [
        (
            item["source_name"],
            item["source_region"],
            item["source_reliability"],
            item["title"],
            item.get("summary", ""),
            item["url"],
            item.get("published_at", ""),
            ",".join(item.get("tags", [])),
        )
        for item in items
    ]
    try:
        with mysql_connection(config, with_database=True) as connection:
            cursor = connection.cursor()
            cursor.executemany(query, values)
            inserted = cursor.rowcount
            cursor.close()
        return max(inserted, 0), f"Stored {max(inserted, 0)} new rows in MySQL."
    except Exception as exc:
        return 0, str(exc)


def load_fact_items(limit: int = 60, search: str = "", region: str = "All") -> tuple[list[dict[str, object]], str]:
    ok, message = initialize_database()
    if not ok:
        return [], message
    clauses: list[str] = []
    params: list[object] = []
    if search.strip():
        clauses.append("(title LIKE %s OR summary LIKE %s OR source_name LIKE %s)")
        needle = f"%{search.strip()}%"
        params.extend([needle, needle, needle])
    if region != "All":
        clauses.append("source_region = %s")
        params.append(region)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"""
        SELECT source_name, source_region, source_reliability, title, summary, url, published_at, fetched_at, tags
        FROM fact_check_items
        {where}
        ORDER BY id DESC
        LIMIT %s
    """
    params.append(limit)
    try:
        with mysql_connection(with_database=True) as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
        return rows, "Loaded from MySQL."
    except Exception as exc:
        return [], str(exc)


def find_evidence_candidates(query_text: str, region: str = "All", limit: int = 8) -> tuple[list[dict[str, object]], str]:
    words = [
        word
        for word in re.findall(r"[A-Za-z0-9]+", query_text.lower())
        if len(word) >= 4 and word not in {"that", "this", "with", "from", "have", "will", "claim", "viral"}
    ]
    keywords = list(dict.fromkeys(words))[:8]
    if not keywords:
        return [], "No searchable keywords found in the claim."

    ok, message = initialize_database()
    if not ok:
        return [], message

    keyword_clauses = []
    params: list[object] = []
    for keyword in keywords:
        keyword_clauses.append("(LOWER(title) LIKE %s OR LOWER(summary) LIKE %s OR LOWER(source_name) LIKE %s OR LOWER(tags) LIKE %s)")
        needle = f"%{keyword}%"
        params.extend([needle, needle, needle, needle])
    where = f"({' OR '.join(keyword_clauses)})"
    if region != "All":
        where = f"{where} AND source_region = %s"
        params.append(region)

    query = f"""
        SELECT source_name, source_region, source_reliability, title, summary, url, published_at, fetched_at, tags
        FROM fact_check_items
        WHERE {where}
        ORDER BY source_reliability DESC, id DESC
        LIMIT %s
    """
    params.append(limit)
    try:
        with mysql_connection(with_database=True) as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
        return rows, f"Matched stored trusted-source data using: {', '.join(keywords)}"
    except Exception as exc:
        return [], str(exc)
