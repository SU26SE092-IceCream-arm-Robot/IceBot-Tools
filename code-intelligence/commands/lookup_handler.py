import sys
import argparse
from pathlib import Path

# Add project root to path to allow importing codeintel and toolcore
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))

from codeintel.queries import query_handlers

def main():
    parser = argparse.ArgumentParser(description="Lookup CQRS Command/Query Handlers in the SQLite index")
    parser.add_argument("query", type=str, help="Handler name or substring to search for")
    parser.add_argument("--context", type=str, default=None, help="Filter by bounded context")
    
    args = parser.parse_args()
    
    try:
        results = query_handlers(args.query, context_filter=args.context)
        if not results:
            print(f"No handlers found matching: '{args.query}'" + (f" under context '{args.context}'" if args.context else ""))
            return
            
        print(f"Found {len(results)} matching handlers:\n")
        for idx, h in enumerate(results, 1):
            print(f"{idx}. [{h['handler_type'].upper()}] {h['handler_name']}")
            print(f"   Context   : {h['bounded_context'] or 'None'}")
            if h.get('request_name'):
                print(f"   Request   : {h['request_name']}")
            if h.get('result_name'):
                print(f"   Result    : {h['result_name']}")
            print(f"   Location  : {h['relative_path']} (Line: {h['line_start']})")
            
            # Store dependencies
            if h.get("store_dependencies"):
                print(f"   Uses Stores:")
                for store in h["store_dependencies"]:
                    print(f"     - {store}")
                    
            # Callers
            if h.get("caller_controllers") or h.get("caller_graphql"):
                print(f"   Triggered By:")
                for ctrl in h.get("caller_controllers", []):
                    print(f"     - Controller: {ctrl}")
                for gf in h.get("caller_graphql", []):
                    print(f"     - GraphQL Field: {gf['field_type'].upper()} '{gf['field_name']}' via resolver '{gf['resolver']}'")
                    
            print("-" * 60)
            
    except Exception as e:
        print(f"Lookup error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
