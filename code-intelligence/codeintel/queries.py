import sqlite3
from codeintel.config import DB_PATH
from codeintel.db import get_connection

def query_symbols(query_str: str) -> list:
    """Finds symbols matching the query string (case-insensitive substring match)."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Match name or full_name
        cursor.execute("""
            SELECT s.*, f.relative_path, f.source_path 
            FROM symbols s
            JOIN indexed_files f ON s.file_id = f.file_id
            WHERE s.name LIKE ? OR s.full_name LIKE ?
            ORDER BY s.kind, s.name
            LIMIT 50
        """, (f"%{query_str}%", f"%{query_str}%"))
        results = [dict(row) for row in cursor.fetchall()]
        
        # Enriched with store information where applicable
        for r in results:
            if r["name"].endswith("Store"):
                cursor.execute("""
                    SELECT interface_name, implementation_name 
                    FROM stores 
                    WHERE interface_name = ? OR implementation_name = ?
                """, (r["name"], r["name"]))
                store = cursor.fetchone()
                if store:
                    r["related_store"] = dict(store)
                    
        return results
    finally:
        conn.close()

def query_endpoints(query_str: str) -> list:
    """Finds endpoints matching the query string in route, controller, or action."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT e.*, f.relative_path, f.source_path 
            FROM endpoints e
            JOIN indexed_files f ON e.file_id = f.file_id
            WHERE e.route LIKE ? OR e.controller LIKE ? OR e.action LIKE ?
            ORDER BY e.route
            LIMIT 50
        """, (f"%{query_str}%", f"%{query_str}%", f"%{query_str}%"))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def query_handlers(query_str: str, context_filter: str = None) -> list:
    """Finds handlers matching query_str, optionally filtering by bounded_context."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Match handler name
        sql = """
            SELECT h.*, f.relative_path, f.source_path 
            FROM handlers h
            JOIN indexed_files f ON h.file_id = f.file_id
            WHERE h.handler_name LIKE ?
        """
        params = [f"%{query_str}%"]
        
        if context_filter:
            sql += " AND h.bounded_context = ?"
            params.append(context_filter)
            
        sql += " ORDER BY h.handler_name LIMIT 50"
        
        cursor.execute(sql, params)
        handlers = [dict(row) for row in cursor.fetchall()]
        
        # Enrich each handler with its store dependencies and caller endpoints
        for h in handlers:
            name = h["handler_name"]
            
            # Find store dependencies using relationships
            cursor.execute("""
                SELECT to_name as store_name FROM relationships 
                WHERE from_name = ? AND relation_type = 'uses_store'
            """, (name,))
            h["store_dependencies"] = [row["store_name"] for row in cursor.fetchall()]
            
            # Find related WebAPI controllers calling this handler (constructor injection)
            cursor.execute("""
                SELECT from_name as controller_name FROM relationships
                WHERE to_name = ? AND relation_type = 'calls_handler' AND from_kind = 'controller'
            """, (name,))
            h["caller_controllers"] = [row["controller_name"] for row in cursor.fetchall()]
            
            # Find related GraphQL query/mutation fields mapping to this handler
            cursor.execute("""
                SELECT field_name, field_type, resolver FROM graphql_fields
                WHERE handler_name = ?
            """, (name,))
            h["caller_graphql"] = [dict(row) for row in cursor.fetchall()]
            
        return handlers
    finally:
        conn.close()

def get_all_symbols() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM symbols")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_all_endpoints() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM endpoints")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_all_relationships() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM relationships")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
