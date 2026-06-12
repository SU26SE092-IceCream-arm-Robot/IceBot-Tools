import sys
import argparse
from pathlib import Path

# Add project root to path to allow importing codeintel and toolcore
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))

from codeintel.queries import query_endpoints

def main():
    parser = argparse.ArgumentParser(description="Lookup WebAPI endpoints in the SQLite index")
    parser.add_argument("query", type=str, help="Route, controller, or action substring to search for")
    
    args = parser.parse_args()
    
    try:
        results = query_endpoints(args.query)
        if not results:
            print(f"No endpoints found matching: '{args.query}'")
            return
            
        print(f"Found {len(results)} matching endpoints:\n")
        for idx, ep in enumerate(results, 1):
            print(f"{idx}. [{ep['http_method']}] {ep['route']}")
            print(f"   Controller: {ep['controller']}")
            print(f"   Action    : {ep['action']}")
            print(f"   Project   : {ep['project_key']} (Context: {ep['bounded_context'] or 'None'})")
            if ep.get('api_version'):
                print(f"   API Ver.  : {ep['api_version']}")
            print(f"   Auth Type : {ep['auth_type']}")
            if ep.get('policy'):
                print(f"   Policy    : {ep['policy']}")
            if ep.get('handler_name'):
                print(f"   Handler   : {ep['handler_name']}")
            print(f"   Location  : {ep['relative_path']} (Line: {ep['line_start']})")
            print("-" * 60)
            
    except Exception as e:
        print(f"Lookup error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
