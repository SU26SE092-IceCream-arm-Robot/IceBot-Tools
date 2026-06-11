import re
import sqlite3
from codeintel.config import DB_PATH

def check_db_for_word(word: str) -> str or None:
    """Checks the database to see if the word corresponds to a known symbol, endpoint, or handler.
    Returns the classification ('symbol', 'endpoint', 'handler') or None."""
    if not DB_PATH.exists():
        return None
        
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Check handlers
        cursor.execute("SELECT handler_name FROM handlers WHERE handler_name = ? LIMIT 1", (word,))
        if cursor.fetchone():
            return "handler"
            
        # 2. Check stores
        cursor.execute("SELECT interface_name, implementation_name FROM stores WHERE interface_name = ? OR implementation_name = ? LIMIT 1", (word, word))
        if cursor.fetchone():
            return "symbol"
            
        # 3. Check symbols
        cursor.execute("SELECT name, kind FROM symbols WHERE name = ? LIMIT 1", (word,))
        row = cursor.fetchone()
        if row:
            kind = row["kind"]
            if kind in ('controller', 'method') and "Controller" in word:
                return "endpoint"
            return "symbol"
            
        # 4. Check route matches
        cursor.execute("SELECT route FROM endpoints WHERE route LIKE ? LIMIT 1", (f"%{word}%",))
        if cursor.fetchone():
            return "endpoint"
            
        return None
    except Exception:
        # Gracefully handle database locks, connection errors, or uninitialized tables
        return None
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def classify_code_intent(query: str) -> dict:
    """Classifies the user query to decide if it should route to the structural code index or semantic RAG."""
    query_clean = query.strip()
    
    # 1. SQLite index check for exact words in the query
    # Tokenize query into alphanumeric words, ignoring common short words/stop words
    words = re.findall(r'\b[A-Za-z_]\w*\b', query_clean)
    for word in words:
        if len(word) < 4:
            continue
            
        matched_type = check_db_for_word(word)
        if matched_type:
            return {
                "suggested_source": "code-index",
                "reason": f"Query contains the term '{word}' found as a {matched_type} in the code index.",
                "lookup_type": matched_type,
                "matched_term": word
            }
            
    # 2. Keyword heuristic checks
    query_lower = query_clean.lower()
    
    # Endpoint keywords
    endpoint_keywords = ['controller', 'route', 'endpoint', 'api/', 'api_version', 'http', 'get ', 'post ', 'put ', 'delete ']
    if any(kw in query_lower for kw in endpoint_keywords):
        return {
            "suggested_source": "code-index",
            "reason": "Query contains endpoint or routing-related keywords.",
            "lookup_type": "endpoint"
        }
        
    # Handler keywords
    handler_keywords = ['handler', 'command', 'query handler', 'command handler', 'cqrs', 'handleasync', 'handle']
    if any(kw in query_lower for kw in handler_keywords):
        return {
            "suggested_source": "code-index",
            "reason": "Query contains CQRS command/query handler keywords.",
            "lookup_type": "handler"
        }
        
    # Symbol keywords
    symbol_keywords = ['store', 'interface', 'class ', 'struct ', 'record ', 'enum ', 'symbol', 'implements', 'injects', 'dependency injection']
    if any(kw in query_lower for kw in symbol_keywords):
        return {
            "suggested_source": "code-index",
            "reason": "Query contains code symbol or interface definition keywords.",
            "lookup_type": "symbol"
        }
        
    # Default to semantic RAG
    return {
        "suggested_source": "rag",
        "reason": "Default query classification (semantic text search).",
        "lookup_type": None
    }
