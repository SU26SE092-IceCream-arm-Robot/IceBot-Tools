import sqlite3
from codeintel.db import get_db_conn

SCHEMA_STATEMENTS = [
    # 1. indexed_files
    """
    CREATE TABLE IF NOT EXISTS indexed_files (
        id TEXT PRIMARY KEY,
        repository_key TEXT NOT NULL,
        project_key TEXT,
        language TEXT NOT NULL,
        source_root TEXT NOT NULL,
        source_path TEXT NOT NULL,
        relative_path TEXT NOT NULL,
        file_id TEXT NOT NULL,
        file_hash TEXT NOT NULL,
        indexed_at TEXT NOT NULL,
        status TEXT NOT NULL
    );
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_indexed_files_repo_file_id ON indexed_files(repository_key, file_id);",
    "CREATE INDEX IF NOT EXISTS idx_indexed_files_file_hash ON indexed_files(file_hash);",
    "CREATE INDEX IF NOT EXISTS idx_indexed_files_language ON indexed_files(language);",
    "CREATE INDEX IF NOT EXISTS idx_indexed_files_project_key ON indexed_files(project_key);",

    # 2. symbols
    """
    CREATE TABLE IF NOT EXISTS symbols (
        id TEXT PRIMARY KEY,
        file_id TEXT NOT NULL,
        repository_key TEXT NOT NULL,
        project_key TEXT,
        bounded_context TEXT,
        language TEXT NOT NULL,
        kind TEXT NOT NULL,
        name TEXT NOT NULL,
        full_name TEXT,
        namespace TEXT,
        containing_type TEXT,
        signature TEXT,
        line_start INTEGER,
        line_end INTEGER
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);",
    "CREATE INDEX IF NOT EXISTS idx_symbols_full_name ON symbols(full_name);",
    "CREATE INDEX IF NOT EXISTS idx_symbols_kind ON symbols(kind);",
    "CREATE INDEX IF NOT EXISTS idx_symbols_bounded_context ON symbols(bounded_context);",
    "CREATE INDEX IF NOT EXISTS idx_symbols_repo_proj ON symbols(repository_key, project_key);",

    # 3. endpoints
    """
    CREATE TABLE IF NOT EXISTS endpoints (
        id TEXT PRIMARY KEY,
        repository_key TEXT NOT NULL,
        project_key TEXT,
        bounded_context TEXT,
        http_method TEXT,
        route TEXT NOT NULL,
        api_version TEXT,
        controller TEXT,
        action TEXT,
        auth_type TEXT,
        policy TEXT,
        handler_name TEXT,
        file_id TEXT NOT NULL,
        line_start INTEGER
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_endpoints_route ON endpoints(route);",
    "CREATE INDEX IF NOT EXISTS idx_endpoints_controller ON endpoints(controller);",
    "CREATE INDEX IF NOT EXISTS idx_endpoints_policy ON endpoints(policy);",
    "CREATE INDEX IF NOT EXISTS idx_endpoints_auth_type ON endpoints(auth_type);",
    "CREATE INDEX IF NOT EXISTS idx_endpoints_bounded_context ON endpoints(bounded_context);",

    # 4. graphql_fields
    """
    CREATE TABLE IF NOT EXISTS graphql_fields (
        id TEXT PRIMARY KEY,
        repository_key TEXT NOT NULL,
        bounded_context TEXT,
        field_type TEXT NOT NULL,
        field_name TEXT NOT NULL,
        resolver TEXT,
        auth_type TEXT,
        policy TEXT,
        handler_name TEXT,
        file_id TEXT NOT NULL,
        line_start INTEGER
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_graphql_fields_name ON graphql_fields(field_name);",
    "CREATE INDEX IF NOT EXISTS idx_graphql_fields_type ON graphql_fields(field_type);",
    "CREATE INDEX IF NOT EXISTS idx_graphql_fields_policy ON graphql_fields(policy);",
    "CREATE INDEX IF NOT EXISTS idx_graphql_fields_bounded_context ON graphql_fields(bounded_context);",

    # 5. handlers
    """
    CREATE TABLE IF NOT EXISTS handlers (
        id TEXT PRIMARY KEY,
        repository_key TEXT NOT NULL,
        project_key TEXT,
        handler_name TEXT NOT NULL,
        handler_type TEXT,
        request_name TEXT,
        result_name TEXT,
        bounded_context TEXT,
        file_id TEXT NOT NULL,
        line_start INTEGER
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_handlers_name ON handlers(handler_name);",
    "CREATE INDEX IF NOT EXISTS idx_handlers_bounded_context ON handlers(bounded_context);",

    # 6. stores
    """
    CREATE TABLE IF NOT EXISTS stores (
        id TEXT PRIMARY KEY,
        repository_key TEXT NOT NULL,
        interface_name TEXT,
        implementation_name TEXT,
        bounded_context TEXT,
        interface_file_id TEXT,
        implementation_file_id TEXT
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_stores_interface ON stores(interface_name);",
    "CREATE INDEX IF NOT EXISTS idx_stores_implementation ON stores(implementation_name);",
    "CREATE INDEX IF NOT EXISTS idx_stores_bounded_context ON stores(bounded_context);",

    # 7. relationships
    """
    CREATE TABLE IF NOT EXISTS relationships (
        id TEXT PRIMARY KEY,
        repository_key TEXT NOT NULL,
        from_kind TEXT NOT NULL,
        from_name TEXT NOT NULL,
        from_context TEXT,
        to_kind TEXT NOT NULL,
        to_name TEXT NOT NULL,
        to_context TEXT,
        relation_type TEXT NOT NULL,
        evidence_file_id TEXT,
        line_start INTEGER
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_relationships_from ON relationships(from_name);",
    "CREATE INDEX IF NOT EXISTS idx_relationships_to ON relationships(to_name);",
    "CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relation_type);",

    # 8. index_runs
    """
    CREATE TABLE IF NOT EXISTS index_runs (
        id TEXT PRIMARY KEY,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        repository_key TEXT,
        files_scanned INTEGER,
        files_indexed INTEGER,
        files_skipped INTEGER,
        status TEXT NOT NULL,
        message TEXT
    );
    """
]

def init_db(conn: sqlite3.Connection):
    """Initializes the database schema using the provided connection."""
    cursor = conn.cursor()
    for statement in SCHEMA_STATEMENTS:
        cursor.execute(statement)

def init_db_if_needed():
    """Conencts and initializes database schema if tables don't exist."""
    with get_db_conn() as conn:
        init_db(conn)
