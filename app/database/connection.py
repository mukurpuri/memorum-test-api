import os
import threading
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime
import sqlite3


class DatabaseConnection:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()
    
    def connect(self) -> None:
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.connection_string,
                check_same_thread=False
            )
            self._connection.row_factory = sqlite3.Row
    
    def disconnect(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            self.connect()
            return self._connection.execute(query, params)
    
    def executemany(self, query: str, params_list: List[tuple]) -> sqlite3.Cursor:
        with self._lock:
            self.connect()
            return self._connection.executemany(query, params_list)
    
    def commit(self) -> None:
        if self._connection:
            self._connection.commit()
    
    def rollback(self) -> None:
        if self._connection:
            self._connection.rollback()
    
    @contextmanager
    def transaction(self):
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise


class ConnectionPool:
    def __init__(
        self,
        connection_string: str,
        min_connections: int = 2,
        max_connections: int = 10,
    ):
        self.connection_string = connection_string
        self.min_connections = min_connections
        self.max_connections = max_connections
        self._pool: List[DatabaseConnection] = []
        self._in_use: List[DatabaseConnection] = []
        self._lock = threading.RLock()
        self._stats = {
            "connections_created": 0,
            "connections_reused": 0,
            "peak_usage": 0,
        }
        
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        for _ in range(self.min_connections):
            conn = DatabaseConnection(self.connection_string)
            conn.connect()
            self._pool.append(conn)
            self._stats["connections_created"] += 1
    
    def acquire(self) -> DatabaseConnection:
        with self._lock:
            if self._pool:
                conn = self._pool.pop()
                self._in_use.append(conn)
                self._stats["connections_reused"] += 1
            elif len(self._in_use) < self.max_connections:
                conn = DatabaseConnection(self.connection_string)
                conn.connect()
                self._in_use.append(conn)
                self._stats["connections_created"] += 1
            else:
                raise RuntimeError("Connection pool exhausted")
            
            current_usage = len(self._in_use)
            if current_usage > self._stats["peak_usage"]:
                self._stats["peak_usage"] = current_usage
            
            return conn
    
    def release(self, conn: DatabaseConnection) -> None:
        with self._lock:
            if conn in self._in_use:
                self._in_use.remove(conn)
                self._pool.append(conn)
    
    @contextmanager
    def connection(self):
        conn = self.acquire()
        try:
            yield conn
        finally:
            self.release(conn)
    
    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "pool_size": len(self._pool),
                "in_use": len(self._in_use),
                "min_connections": self.min_connections,
                "max_connections": self.max_connections,
                **self._stats,
            }
    
    def close_all(self) -> None:
        with self._lock:
            for conn in self._pool + self._in_use:
                conn.disconnect()
            self._pool.clear()
            self._in_use.clear()


db_pool = ConnectionPool(
    os.getenv("DATABASE_URL", ":memory:"),
    min_connections=2,
    max_connections=10,
)


def get_db() -> DatabaseConnection:
    return db_pool.acquire()
