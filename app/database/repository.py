from typing import Generic, TypeVar, Optional, List, Dict, Any
from abc import ABC, abstractmethod
from datetime import datetime

from app.database.connection import db_pool

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    table_name: str = ""
    
    def __init__(self):
        if not self.table_name:
            raise ValueError("table_name must be set")
    
    @abstractmethod
    def _row_to_entity(self, row: Dict[str, Any]) -> T:
        pass
    
    @abstractmethod
    def _entity_to_row(self, entity: T) -> Dict[str, Any]:
        pass
    
    def find_by_id(self, id: int) -> Optional[T]:
        with db_pool.connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE id = ?",
                (id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_entity(dict(row))
            return None
    
    def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        with db_pool.connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.table_name} LIMIT ? OFFSET ?",
                (limit, offset)
            )
            return [self._row_to_entity(dict(row)) for row in cursor.fetchall()]
    
    def find_by(self, **conditions) -> List[T]:
        where_clauses = []
        values = []
        
        for key, value in conditions.items():
            where_clauses.append(f"{key} = ?")
            values.append(value)
        
        where_sql = " AND ".join(where_clauses)
        
        with db_pool.connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE {where_sql}",
                tuple(values)
            )
            return [self._row_to_entity(dict(row)) for row in cursor.fetchall()]
    
    def find_one_by(self, **conditions) -> Optional[T]:
        results = self.find_by(**conditions)
        return results[0] if results else None
    
    def create(self, entity: T) -> T:
        row = self._entity_to_row(entity)
        columns = list(row.keys())
        placeholders = ", ".join(["?" for _ in columns])
        columns_sql = ", ".join(columns)
        
        with db_pool.connection() as conn:
            cursor = conn.execute(
                f"INSERT INTO {self.table_name} ({columns_sql}) VALUES ({placeholders})",
                tuple(row.values())
            )
            conn.commit()
            
            new_id = cursor.lastrowid
            return self.find_by_id(new_id)
    
    def update(self, id: int, updates: Dict[str, Any]) -> Optional[T]:
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        values.append(id)
        set_sql = ", ".join(set_clauses)
        
        with db_pool.connection() as conn:
            conn.execute(
                f"UPDATE {self.table_name} SET {set_sql} WHERE id = ?",
                tuple(values)
            )
            conn.commit()
        
        return self.find_by_id(id)
    
    def delete(self, id: int) -> bool:
        with db_pool.connection() as conn:
            cursor = conn.execute(
                f"DELETE FROM {self.table_name} WHERE id = ?",
                (id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def count(self, **conditions) -> int:
        if conditions:
            where_clauses = []
            values = []
            for key, value in conditions.items():
                where_clauses.append(f"{key} = ?")
                values.append(value)
            where_sql = " WHERE " + " AND ".join(where_clauses)
        else:
            where_sql = ""
            values = []
        
        with db_pool.connection() as conn:
            cursor = conn.execute(
                f"SELECT COUNT(*) FROM {self.table_name}{where_sql}",
                tuple(values)
            )
            return cursor.fetchone()[0]
    
    def exists(self, **conditions) -> bool:
        return self.count(**conditions) > 0
