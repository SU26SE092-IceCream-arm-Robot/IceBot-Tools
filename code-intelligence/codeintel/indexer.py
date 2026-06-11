import time
from datetime import datetime
import uuid
import sqlite3
from pathlib import Path
from codeintel.config import load_sources_config, DB_PATH
from codeintel.db import get_db_conn
from codeintel.schema import init_db, init_db_if_needed
from codeintel.source_loader import scan_source_files, infer_bounded_context
from codeintel.csharp_scanner import scan_csharp_file
from codeintel.markdown_scanner import scan_markdown_file

def clear_file_data(conn: sqlite3.Connection, file_id: str):
    """Deletes all parsed records associated with a specific file_id."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM symbols WHERE file_id = ?", (file_id,))
    cursor.execute("DELETE FROM endpoints WHERE file_id = ?", (file_id,))
    cursor.execute("DELETE FROM graphql_fields WHERE file_id = ?", (file_id,))
    cursor.execute("DELETE FROM handlers WHERE file_id = ?", (file_id,))
    cursor.execute("DELETE FROM relationships WHERE evidence_file_id = ?", (file_id,))

def rebuild_stores(conn: sqlite3.Connection, repo_key: str):
    """Rebuilds the stores table by pairing interface and implementation stores."""
    cursor = conn.cursor()
    
    # 1. Fetch all store interfaces
    cursor.execute("""
        SELECT name, file_id, bounded_context FROM symbols 
        WHERE repository_key = ? AND kind = 'interface' AND name LIKE '%Store'
    """, (repo_key,))
    interfaces = {row["name"]: dict(row) for row in cursor.fetchall()}
    
    # 2. Fetch all store implementations
    cursor.execute("""
        SELECT name, file_id, bounded_context FROM symbols 
        WHERE repository_key = ? AND kind = 'class' AND name LIKE '%Store'
    """, (repo_key,))
    implementations = {row["name"]: dict(row) for row in cursor.fetchall()}
    
    # 3. Fetch implements relationships
    cursor.execute("""
        SELECT from_name, to_name FROM relationships 
        WHERE repository_key = ? AND relation_type = 'implements'
          AND from_name LIKE '%Store' AND to_name LIKE '%Store'
    """, (repo_key,))
    relationships_implements = cursor.fetchall()
    
    paired_implementations = set()
    paired_interfaces = set()
    pairs = []
    
    # Match style 1: class implements interface
    for rel in relationships_implements:
        impl_name = rel["from_name"]
        iface_name = rel["to_name"]
        
        if impl_name in implementations and iface_name in interfaces:
            impl = implementations[impl_name]
            iface = interfaces[iface_name]
            
            pairs.append({
                "interface_name": iface_name,
                "implementation_name": impl_name,
                "bounded_context": impl["bounded_context"] or iface["bounded_context"],
                "interface_file_id": iface["file_id"],
                "implementation_file_id": impl["file_id"]
            })
            paired_implementations.add(impl_name)
            paired_interfaces.add(iface_name)
            
    # Match style 2: name mapping fallback (XStore -> IXStore)
    for impl_name, impl in implementations.items():
        if impl_name in paired_implementations:
            continue
            
        expected_iface = "I" + impl_name
        if expected_iface in interfaces and expected_iface not in paired_interfaces:
            iface = interfaces[expected_iface]
            pairs.append({
                "interface_name": expected_iface,
                "implementation_name": impl_name,
                "bounded_context": impl["bounded_context"] or iface["bounded_context"],
                "interface_file_id": iface["file_id"],
                "implementation_file_id": impl["file_id"]
            })
            paired_implementations.add(impl_name)
            paired_interfaces.add(expected_iface)
            
    # Add unmatched implementations
    for impl_name, impl in implementations.items():
        if impl_name not in paired_implementations:
            pairs.append({
                "interface_name": None,
                "implementation_name": impl_name,
                "bounded_context": impl["bounded_context"],
                "interface_file_id": None,
                "implementation_file_id": impl["file_id"]
            })
            
    # Add unmatched interfaces
    for iface_name, iface in interfaces.items():
        if iface_name not in paired_interfaces:
            pairs.append({
                "interface_name": iface_name,
                "implementation_name": None,
                "bounded_context": iface["bounded_context"],
                "interface_file_id": iface["file_id"],
                "implementation_file_id": None
            })
            
    # Delete existing store entries and insert new ones
    cursor.execute("DELETE FROM stores WHERE repository_key = ?", (repo_key,))
    for p in pairs:
        cursor.execute("""
            INSERT INTO stores (id, repository_key, interface_name, implementation_name, bounded_context, interface_file_id, implementation_file_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), repo_key, p["interface_name"], p["implementation_name"], p["bounded_context"], p["interface_file_id"], p["implementation_file_id"]))

def run_indexing(source_key: str = None, rebuild: bool = False, dry_run: bool = False) -> dict:
    """Runs the code indexer pipeline for all enabled or a specific source repository."""
    start_time = time.time()
    run_id = str(uuid.uuid4())
    started_at = datetime.utcnow().isoformat()
    
    # Initialize DB (if not dry run)
    if not dry_run:
        init_db_if_needed()
        
    # Load configuration
    sources = load_sources_config()
    if source_key:
        sources = [s for s in sources if s["repository_key"] == source_key]
        if not sources:
            raise ValueError(f"No source configured with repository key '{source_key}'")
            
    # Filter only enabled sources
    sources = [s for s in sources if s["enabled"]]
    if not sources:
        return {"message": "No enabled sources to index."}
        
    # Stats tracking
    stats = {
        "files_scanned": 0,
        "files_indexed": 0,
        "files_skipped": 0,
        "symbols": 0,
        "endpoints": 0,
        "graphql_fields": 0,
        "handlers": 0,
        "stores": 0,
        "relationships": 0,
        "duration": 0.0
    }
    
    # Connect to database (mock connection if dry run)
    conn = None
    if not dry_run:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON;")
        
        # Log run start
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO index_runs (id, started_at, status, files_scanned, files_indexed, files_skipped)
            VALUES (?, ?, 'running', 0, 0, 0)
        """, (run_id, started_at))
        conn.commit()
        
    try:
        for source in sources:
            repo_key = source["repository_key"]
            
            # Scan files from disk
            disk_files = scan_source_files(source)
            stats["files_scanned"] += len(disk_files)
            
            # Get existing files from DB (to check hashes)
            db_hashes = {}
            if conn and not rebuild:
                cursor = conn.cursor()
                cursor.execute("SELECT file_id, file_hash FROM indexed_files WHERE repository_key = ?", (repo_key,))
                db_hashes = {row["file_id"]: row["file_hash"] for row in cursor.fetchall()}
                
            scanned_file_ids = set()
            
            for file_meta in disk_files:
                file_id = file_meta["file_id"]
                file_hash = file_meta["file_hash"]
                scanned_file_ids.add(file_id)
                
                # Check cache (incremental)
                if not rebuild and file_id in db_hashes and db_hashes[file_id] == file_hash:
                    stats["files_skipped"] += 1
                    continue
                    
                stats["files_indexed"] += 1
                
                # Read content and parse
                file_path = Path(file_meta["source_path"])
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                if file_meta["language"] == "csharp":
                    bounded_context = infer_bounded_context(file_meta["relative_path"])
                    parsed = scan_csharp_file(content, file_id, repo_key, file_meta["project_key"], bounded_context)
                elif file_meta["language"] == "markdown":
                    parsed = scan_markdown_file(content, file_id, repo_key, file_meta["project_key"])
                else:
                    parsed = {
                        "symbols": [],
                        "endpoints": [],
                        "graphql_fields": [],
                        "handlers": [],
                        "stores_raw": [],
                        "relationships": []
                    }
                    
                if dry_run:
                    # Accumulate dry stats
                    stats["symbols"] += len(parsed["symbols"])
                    stats["endpoints"] += len(parsed["endpoints"])
                    stats["graphql_fields"] += len(parsed["graphql_fields"])
                    stats["handlers"] += len(parsed["handlers"])
                    stats["relationships"] += len(parsed["relationships"])
                else:
                    # Update database
                    cursor = conn.cursor()
                    
                    # 1. Clean up old records for this file
                    clear_file_data(conn, file_id)
                    
                    # 2. Insert File Entry
                    cursor.execute("""
                        INSERT OR REPLACE INTO indexed_files (id, repository_key, project_key, language, source_root, source_path, relative_path, file_id, file_hash, indexed_at, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (str(uuid.uuid4()), repo_key, file_meta["project_key"], file_meta["language"], file_meta["source_root"], file_meta["source_path"], file_meta["relative_path"], file_id, file_hash, datetime.utcnow().isoformat(), "active"))
                    
                    # 3. Insert Symbols
                    for sym in parsed["symbols"]:
                        cursor.execute("""
                            INSERT INTO symbols (id, file_id, repository_key, project_key, bounded_context, language, kind, name, full_name, namespace, containing_type, signature, line_start, line_end)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (sym["id"], sym["file_id"], sym["repository_key"], sym["project_key"], sym["bounded_context"], sym["language"], sym["kind"], sym["name"], sym["full_name"], sym["namespace"], sym["containing_type"], sym["signature"], sym["line_start"], sym["line_end"]))
                        
                    # 4. Insert Endpoints
                    for ep in parsed["endpoints"]:
                        cursor.execute("""
                            INSERT INTO endpoints (id, repository_key, project_key, bounded_context, http_method, route, api_version, controller, action, auth_type, policy, handler_name, file_id, line_start)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (ep["id"], ep["repository_key"], ep["project_key"], ep["bounded_context"], ep["http_method"], ep["route"], ep["api_version"], ep["controller"], ep["action"], ep["auth_type"], ep["policy"], ep["handler_name"], ep["file_id"], ep["line_start"]))
                        
                    # 5. Insert GraphQL fields
                    for gf in parsed["graphql_fields"]:
                        cursor.execute("""
                            INSERT INTO graphql_fields (id, repository_key, bounded_context, field_type, field_name, resolver, auth_type, policy, handler_name, file_id, line_start)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (gf["id"], gf["repository_key"], gf["bounded_context"], gf["field_type"], gf["field_name"], gf["resolver"], gf["auth_type"], gf["policy"], gf["handler_name"], gf["file_id"], gf["line_start"]))
                        
                    # 6. Insert Handlers
                    for h in parsed["handlers"]:
                        cursor.execute("""
                            INSERT INTO handlers (id, repository_key, project_key, handler_name, handler_type, request_name, result_name, bounded_context, file_id, line_start)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (h["id"], h["repository_key"], h["project_key"], h["handler_name"], h["handler_type"], h["request_name"], h["result_name"], h["bounded_context"], h["file_id"], h["line_start"]))
                        
                    # 7. Insert Relationships
                    for r in parsed["relationships"]:
                        cursor.execute("""
                            INSERT INTO relationships (id, repository_key, from_kind, from_name, from_context, to_kind, to_name, to_context, relation_type, evidence_file_id, line_start)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (r["id"], r["repository_key"], r["from_kind"], r["from_name"], r["from_context"], r["to_kind"], r["to_name"], r["to_context"], r["relation_type"], r["evidence_file_id"], r["line_start"]))
                        
            # Clean up deleted (orphaned) files and their references
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT file_id, relative_path FROM indexed_files WHERE repository_key = ?", (repo_key,))
                all_indexed = cursor.fetchall()
                
                for row in all_indexed:
                    db_fid = row["file_id"]
                    if db_fid not in scanned_file_ids:
                        # File was deleted on disk!
                        clear_file_data(conn, db_fid)
                        cursor.execute("DELETE FROM indexed_files WHERE file_id = ?", (db_fid,))
                        
                # Rebuild stores pairing
                rebuild_stores(conn, repo_key)
                conn.commit()
                
        # Gather final counts from DB to print correct stats (if not dry run)
        if conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM symbols")
            stats["symbols"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM endpoints")
            stats["endpoints"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM graphql_fields")
            stats["graphql_fields"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM handlers")
            stats["handlers"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM stores")
            stats["stores"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM relationships")
            stats["relationships"] = cursor.fetchone()[0]
            
        stats["duration"] = time.time() - start_time
        
        # Log completion
        if conn:
            finished_at = datetime.utcnow().isoformat()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE index_runs 
                SET finished_at = ?, status = 'completed', files_scanned = ?, files_indexed = ?, files_skipped = ?, message = ?
                WHERE id = ?
            """, (finished_at, stats["files_scanned"], stats["files_indexed"], stats["files_skipped"], "Index completed successfully", run_id))
            conn.commit()
            
    except Exception as e:
        # Log failure
        if conn:
            finished_at = datetime.utcnow().isoformat()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE index_runs 
                    SET finished_at = ?, status = 'failed', message = ?
                    WHERE id = ?
                """, (finished_at, str(e), run_id))
                conn.commit()
            except:
                pass
        raise e
    finally:
        if conn:
            conn.close()
            
    return stats
