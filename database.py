# database.py
import sqlite3
import logging
from contextlib import contextmanager
import os

DATABASE_FILE = 'file_board.db'
logger = logging.getLogger(__name__)

@contextmanager
def db_connect():
    """Provides a transactional scope around a series of operations."""
    conn = None
    try:
        # Use absolute path to ensure DB is created in the project root
        db_path = os.path.join(os.path.dirname(__file__), DATABASE_FILE)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
        logger.info(f"Database connection established to {db_path}")
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        raise # Re-raise the exception after logging/rollback
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")

def init_db():
    """Initializes the database table if it doesn't exist."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_board (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,          -- Telegram User ID who uploaded
                    chat_id INTEGER NOT NULL,          -- Chat ID where upload happened
                    description TEXT NOT NULL,         -- User-provided description/filename
                    terabox_link TEXT NOT NULL UNIQUE, -- The original Terabox link
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # Add index for faster searching
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_description ON file_board (description);")
            logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize database: {e}")
        # If init fails, the bot probably can't function, so maybe exit or raise
        raise

def add_link(user_id: int, chat_id: int, description: str, terabox_link: str) -> bool:
    """Adds a new link to the file board."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO file_board (user_id, chat_id, description, terabox_link) VALUES (?, ?, ?, ?)",
                (user_id, chat_id, description, terabox_link)
            )
            logger.info(f"Link added by user {user_id}: {description[:50]}...")
            return True
    except sqlite3.IntegrityError:
        logger.warning(f"Attempt to add duplicate Terabox link: {terabox_link}")
        return False # Link already exists
    except sqlite3.Error as e:
        logger.error(f"Failed to add link: {e}")
        return False

def list_links(limit: int = 50) -> list:
    """Lists available links from the board."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, description, timestamp FROM file_board ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            links = cursor.fetchall()
            logger.info(f"Fetched {len(links)} links for listing.")
            # Convert Row objects to dictionaries for easier use
            return [dict(link) for link in links]
    except sqlite3.Error as e:
        logger.error(f"Failed to list links: {e}")
        return []

def search_links(query: str, limit: int = 20) -> list:
    """Searches for links by description."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            # Use FTS5 or simple LIKE for searching. LIKE is simpler for now.
            search_term = f"%{query}%"
            cursor.execute(
                """SELECT id, description, timestamp
                   FROM file_board
                   WHERE description LIKE ?
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (search_term, limit)
            )
            links = cursor.fetchall()
            logger.info(f"Found {len(links)} links matching query '{query}'.")
            return [dict(link) for link in links]
    except sqlite3.Error as e:
        logger.error(f"Failed to search links for '{query}': {e}")
        return []

def get_link_by_id(link_id: int) -> dict | None:
    """Gets the full link details by its database ID."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, description, terabox_link FROM file_board WHERE id = ?", (link_id,))
            link_data = cursor.fetchone()
            if link_data:
                logger.info(f"Fetched link details for ID {link_id}.")
                return dict(link_data)
            else:
                logger.warning(f"No link found with ID {link_id}.")
                return None
    except sqlite3.Error as e:
        logger.error(f"Failed to get link by ID {link_id}: {e}")
        return None

# Ensure DB is initialized when module is loaded (or call explicitly in bot startup)
# init_db() # You might prefer calling this explicitly in bot.py
