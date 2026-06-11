import sys
import sqlite3
import re
from pathlib import Path

# Add project root to path to allow importing codeintel
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from codeintel.config import load_sources_config, DB_PATH
from codeintel.source_loader import scan_source_files

RE_HTTP_ATTRIBUTE = re.compile(r'\[(HttpGet|HttpPost|HttpPut|HttpDelete|HttpPatch)(?:\s*\(|\])')
RE_PUBLIC_METHOD = re.compile(
    r'\bpublic\s+(?:async\s+)?(?:Task\s*<[^>]+>\s*|Task\s+|void\s+|[\w\.<>\?\[\]]+\s+)'
    r'\w+\s*\(',
    re.MULTILINE
)

def count_expected_endpoints(file_path: str) -> int:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return len(RE_HTTP_ATTRIBUTE.findall(content))

def count_expected_graphql_fields(file_path: str) -> int:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if "ExtendObjectType" not in content:
        return 0
    if '"Query"' not in content and '"Mutation"' not in content:
        return 0

    return len(RE_PUBLIC_METHOD.findall(content))

def main():
    if not DB_PATH.exists():
        print("Error: Database does not exist. Please run index_code.py first.", file=sys.stderr)
        sys.exit(1)
        
    try:
        # 1. Load config and scan disk files (using exact indexer rules)
        sources = load_sources_config()
        disk_files = []
        for src in sources:
            if src["enabled"]:
                disk_files.extend(scan_source_files(src))
                
        # 2. Filter target component files from disk scan
        controller_files = [f for f in disk_files if f["relative_path"].endswith("Controller.cs")]
        
        # Handlers must end with Handler.cs and belong to the Application layer (excludes WebAPI custom policy auth handlers)
        handler_files = [f for f in disk_files if f["relative_path"].endswith("Handler.cs") and "Application" in f["relative_path"]]
        
        # Store interfaces must start with 'I' followed by an uppercase letter and end with 'Store.cs'
        store_files = [
            f for f in disk_files 
            if f["relative_path"].endswith("Store.cs") 
            and Path(f["relative_path"]).name.startswith("I") 
            and len(Path(f["relative_path"]).name) > 1 
            and Path(f["relative_path"]).name[1].isupper()
        ]

        endpoint_expectations = {
            f["relative_path"]: count_expected_endpoints(f["source_path"])
            for f in disk_files
            if f["language"] == "csharp"
        }
        endpoint_expectations = {path: count for path, count in endpoint_expectations.items() if count > 0}

        graphql_expectations = {
            f["relative_path"]: count_expected_graphql_fields(f["source_path"])
            for f in disk_files
            if f["language"] == "csharp"
        }
        graphql_expectations = {path: count for path, count in graphql_expectations.items() if count > 0}
        
        # 3. Query the SQLite database for indexed items
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all indexed controller names (symbols where kind = 'class' and name ends with Controller)
        cursor.execute("SELECT name, file_id FROM symbols WHERE kind = 'class' AND name LIKE '%Controller'")
        indexed_controllers = {row["name"]: row["file_id"] for row in cursor.fetchall()}
        
        # Get all indexed handler names (from handlers table)
        cursor.execute("SELECT handler_name, file_id FROM handlers")
        indexed_handlers = {row["handler_name"]: row["file_id"] for row in cursor.fetchall()}
        
        # Get all indexed store interface names (from symbols where kind = 'interface' and name starts with I and ends with Store)
        cursor.execute("SELECT name, file_id FROM symbols WHERE kind = 'interface' AND name LIKE 'I%Store'")
        indexed_stores = {row["name"]: row["file_id"] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT f.relative_path, COUNT(e.id) AS indexed_count
            FROM indexed_files f
            LEFT JOIN endpoints e ON e.file_id = f.file_id
            GROUP BY f.relative_path
        """)
        indexed_endpoint_counts = {row["relative_path"]: row["indexed_count"] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT f.relative_path, COUNT(g.id) AS indexed_count
            FROM indexed_files f
            LEFT JOIN graphql_fields g ON g.file_id = f.file_id
            GROUP BY f.relative_path
        """)
        indexed_graphql_counts = {row["relative_path"]: row["indexed_count"] for row in cursor.fetchall()}
        
        # 4. Perform coverage evaluation
        missing_controllers = []
        for f in controller_files:
            file_name = Path(f["relative_path"]).stem
            if file_name not in indexed_controllers:
                missing_controllers.append(f["relative_path"])
                
        missing_handlers = []
        for f in handler_files:
            file_name = Path(f["relative_path"]).stem
            if file_name not in indexed_handlers:
                missing_handlers.append(f["relative_path"])
                
        missing_stores = []
        for f in store_files:
            file_name = Path(f["relative_path"]).stem
            if file_name not in indexed_stores:
                missing_stores.append(f["relative_path"])

        endpoint_mismatches = []
        indexed_endpoint_total = 0
        expected_endpoint_total = 0
        for relative_path, expected_count in endpoint_expectations.items():
            indexed_count = indexed_endpoint_counts.get(relative_path, 0)
            expected_endpoint_total += expected_count
            indexed_endpoint_total += min(indexed_count, expected_count)
            if indexed_count != expected_count:
                endpoint_mismatches.append((relative_path, expected_count, indexed_count))

        graphql_mismatches = []
        indexed_graphql_total = 0
        expected_graphql_total = 0
        for relative_path, expected_count in graphql_expectations.items():
            indexed_count = indexed_graphql_counts.get(relative_path, 0)
            expected_graphql_total += expected_count
            indexed_graphql_total += min(indexed_count, expected_count)
            if indexed_count != expected_count:
                graphql_mismatches.append((relative_path, expected_count, indexed_count))
                
        # 5. Print coverage report
        total_disk_controllers = len(controller_files)
        indexed_controllers_count = total_disk_controllers - len(missing_controllers)
        controller_pct = (indexed_controllers_count / total_disk_controllers * 100) if total_disk_controllers > 0 else 100.0
        
        total_disk_handlers = len(handler_files)
        indexed_handlers_count = total_disk_handlers - len(missing_handlers)
        handler_pct = (indexed_handlers_count / total_disk_handlers * 100) if total_disk_handlers > 0 else 100.0
        
        total_disk_stores = len(store_files)
        indexed_stores_count = total_disk_stores - len(missing_stores)
        store_pct = (indexed_stores_count / total_disk_stores * 100) if total_disk_stores > 0 else 100.0

        endpoint_pct = (indexed_endpoint_total / expected_endpoint_total * 100) if expected_endpoint_total > 0 else 100.0
        graphql_pct = (indexed_graphql_total / expected_graphql_total * 100) if expected_graphql_total > 0 else 100.0
        
        print("=" * 60)
        print("CODE INDEX COVERAGE REPORT")
        print("=" * 60)
        print(f"Controllers: {indexed_controllers_count} / {total_disk_controllers} ({controller_pct:.1f}%)")
        print(f"Handlers:    {indexed_handlers_count} / {total_disk_handlers} ({handler_pct:.1f}%)")
        print(f"Stores:      {indexed_stores_count} / {total_disk_stores} ({store_pct:.1f}%)")
        print(f"Endpoints:   {indexed_endpoint_total} / {expected_endpoint_total} ({endpoint_pct:.1f}%)")
        print(f"GraphQL:     {indexed_graphql_total} / {expected_graphql_total} ({graphql_pct:.1f}%)")
        
        total_expected = total_disk_controllers + total_disk_handlers + total_disk_stores + expected_endpoint_total + expected_graphql_total
        total_actual = indexed_controllers_count + indexed_handlers_count + indexed_stores_count + indexed_endpoint_total + indexed_graphql_total
        overall_pct = (total_actual / total_expected * 100) if total_expected > 0 else 100.0
        print("-" * 60)
        print(f"Overall Code Coverage: {total_actual} / {total_expected} ({overall_pct:.1f}%)")
        print("=" * 60)
        
        if missing_controllers:
            print("\nMissing Controllers:")
            for mc in missing_controllers:
                print(f"  - {mc}")
                
        if missing_handlers:
            print("\nMissing Handlers:")
            for mh in missing_handlers:
                print(f"  - {mh}")
                
        if missing_stores:
            print("\nMissing Stores:")
            for ms in missing_stores:
                print(f"  - {ms}")

        if endpoint_mismatches:
            print("\nEndpoint Count Mismatches:")
            for path, expected_count, indexed_count in endpoint_mismatches:
                print(f"  - {path}: expected {expected_count}, indexed {indexed_count}")

        if graphql_mismatches:
            print("\nGraphQL Field Count Mismatches:")
            for path, expected_count, indexed_count in graphql_mismatches:
                print(f"  - {path}: expected {expected_count}, indexed {indexed_count}")
                
        conn.close()
        
    except Exception as e:
        print(f"Coverage check failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
