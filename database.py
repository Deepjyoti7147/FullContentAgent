import logging
import time
from typing import Optional, List, Tuple
import psycopg2
from psycopg2 import pool

logger = logging.getLogger("full_content.db")

class DBHandler:
    _pool: Optional[pool.ThreadedConnectionPool] = None

    def __init__(self, dsn: str, min_conn: int = 1, max_conn: int = 3):
        self.dsn = dsn
        self.min_conn = min_conn
        self.max_conn = max_conn

    def connect(self, retries: int = 5, delay: float = 5.0) -> None:
        for attempt in range(1, retries + 1):
            try:
                self._pool = pool.ThreadedConnectionPool(
                    self.min_conn, self.max_conn, dsn=self.dsn, connect_timeout=10
                )
                logger.info("PostgreSQL pool opened")
                return
            except psycopg2.OperationalError as exc:
                logger.warning(f"DB connect attempt {attempt}/{retries} failed: {exc}")
                if attempt < retries:
                    time.sleep(delay)
        raise RuntimeError("Could not connect to PostgreSQL")

    def close(self) -> None:
        if self._pool:
            self._pool.closeall()

    def get_articles_without_content(self, limit: int = 50) -> List[Tuple[int, str]]:
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                # Get articles where raw_content is NULL
                cur.execute(
                    "SELECT id, link FROM news_articles WHERE raw_content IS NULL LIMIT %s",
                    (limit,)
                )
                return cur.fetchall()
        finally:
            self._pool.putconn(conn)

    def update_article_content(self, article_id: int, content: str) -> None:
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE news_articles SET raw_content = %s WHERE id = %s",
                    (content, article_id)
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)
