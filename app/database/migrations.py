from typing import List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
import logging

from app.database.connection import DatabaseConnection, db_pool

logger = logging.getLogger(__name__)


@dataclass
class Migration:
    version: str
    name: str
    up: str
    down: str
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class MigrationRunner:
    MIGRATIONS_TABLE = "_migrations"
    
    def __init__(self):
        self._migrations: List[Migration] = []
        self._ensure_migrations_table()
    
    def _ensure_migrations_table(self) -> None:
        with db_pool.connection() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.MIGRATIONS_TABLE} (
                    version TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def register(self, migration: Migration) -> None:
        self._migrations.append(migration)
        self._migrations.sort(key=lambda m: m.version)
    
    def get_applied_versions(self) -> List[str]:
        with db_pool.connection() as conn:
            cursor = conn.execute(
                f"SELECT version FROM {self.MIGRATIONS_TABLE} ORDER BY version"
            )
            return [row[0] for row in cursor.fetchall()]
    
    def get_pending_migrations(self) -> List[Migration]:
        applied = set(self.get_applied_versions())
        return [m for m in self._migrations if m.version not in applied]
    
    def migrate(self) -> List[str]:
        applied = []
        pending = self.get_pending_migrations()
        
        for migration in pending:
            logger.info(f"Applying migration {migration.version}: {migration.name}")
            
            with db_pool.connection() as conn:
                try:
                    conn.execute(migration.up)
                    conn.execute(
                        f"INSERT INTO {self.MIGRATIONS_TABLE} (version, name) VALUES (?, ?)",
                        (migration.version, migration.name)
                    )
                    conn.commit()
                    applied.append(migration.version)
                    logger.info(f"Migration {migration.version} applied successfully")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Migration {migration.version} failed: {e}")
                    raise
        
        return applied
    
    def rollback(self, steps: int = 1) -> List[str]:
        rolled_back = []
        applied = self.get_applied_versions()
        
        if not applied:
            return rolled_back
        
        to_rollback = applied[-steps:]
        to_rollback.reverse()
        
        for version in to_rollback:
            migration = next((m for m in self._migrations if m.version == version), None)
            if not migration:
                logger.warning(f"Migration {version} not found in registered migrations")
                continue
            
            logger.info(f"Rolling back migration {version}: {migration.name}")
            
            with db_pool.connection() as conn:
                try:
                    conn.execute(migration.down)
                    conn.execute(
                        f"DELETE FROM {self.MIGRATIONS_TABLE} WHERE version = ?",
                        (version,)
                    )
                    conn.commit()
                    rolled_back.append(version)
                    logger.info(f"Migration {version} rolled back successfully")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Rollback of {version} failed: {e}")
                    raise
        
        return rolled_back
    
    def status(self) -> dict:
        applied = self.get_applied_versions()
        pending = self.get_pending_migrations()
        
        return {
            "applied": len(applied),
            "pending": len(pending),
            "applied_versions": applied,
            "pending_versions": [m.version for m in pending],
        }


migration_runner = MigrationRunner()
