import os
import sys
import time
import logging
import urllib.parse
from dotenv import load_dotenv

from database import DBHandler
from fetcher import fetch_full_content

def setup_logging():
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def build_dsn() -> str:
    if os.getenv("POSTGRES_DSN"):
        return os.getenv("POSTGRES_DSN")
    
    user = urllib.parse.quote_plus(os.getenv("POSTGRES_USER", "postgres"))
    password = urllib.parse.quote_plus(os.getenv("POSTGRES_PASSWORD", ""))
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    dbname = os.getenv("POSTGRES_DB", "postgres")
    sslmode = os.getenv("POSTGRES_SSLMODE", "prefer")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"

def run_agent():
    logger = logging.getLogger("full_content.main")
    
    dsn = build_dsn()
    db = DBHandler(dsn=dsn)
    try:
        db.connect()
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

    batch_size = int(os.getenv("BATCH_SIZE", "50"))
    delay_seconds = float(os.getenv("REQUEST_DELAY_SECONDS", "2.0"))
    interval_minutes = int(os.getenv("FETCH_INTERVAL_MINUTES", "5"))
    run_once = os.getenv("RUN_ONCE", "false").lower() == "true"
    
    logger.info(f"Starting FullContentAgent (Batch size: {batch_size})")
    
    try:
        while True:
            logger.info("Checking for articles missing full content...")
            articles = db.get_articles_without_content(limit=batch_size)
            
            if not articles:
                logger.info(f"No articles to process. Sleeping for {interval_minutes} minutes.")
                if run_once:
                    break
                time.sleep(interval_minutes * 60)
                continue
            
            logger.info(f"Found {len(articles)} articles to process.")
            
            success_count = 0
            for article_id, link in articles:
                logger.debug(f"Fetching content for article ID {article_id}: {link}")
                content = fetch_full_content(link)
                
                if content:
                    db.update_article_content(article_id, content)
                success_count += 1
                
                # Polite delay between requests
                time.sleep(delay_seconds)
                
            logger.info(f"Processed {success_count} articles in this batch.")
            
            if run_once:
                break
                
    except KeyboardInterrupt:
        logger.info("Agent stopped by user.")
    finally:
        db.close()
        logger.info("Database connection closed.")

if __name__ == "__main__":
    load_dotenv()
    setup_logging()
    run_agent()
