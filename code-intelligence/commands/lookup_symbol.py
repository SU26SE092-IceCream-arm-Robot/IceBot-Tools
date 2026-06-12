import sys
import argparse
from pathlib import Path

# Add project root to path to allow importing codeintel and toolcore
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))

from codeintel.queries import query_symbols

def main():
    parser = argparse.ArgumentParser(description="Lookup code symbols in the SQLite index")
    parser.add_argument("query", type=str, help="Symbol name or substring to search for")
    
    args = parser.parse_args()
    
    try:
        results = query_symbols(args.query)
        if not results:
            print(f"No symbols found matching: '{args.query}'")
            return
            
        print(f"Found {len(results)} matching symbols:\n")
        for idx, sym in enumerate(results, 1):
            print(f"{idx}. [{sym['kind'].upper()}] {sym['name']}")
            print(f"   Full Name : {sym['full_name']}")
            if sym.get('namespace'):
                print(f"   Namespace : {sym['namespace']}")
            if sym.get('containing_type'):
                print(f"   In Type   : {sym['containing_type']}")
            print(f"   Project   : {sym['project_key']} (Context: {sym['bounded_context'] or 'None'})")
            print(f"   Location  : {sym['relative_path']} (Line: {sym['line_start']})")
            if sym.get('signature'):
                print(f"   Signature : {sym['signature']}")
            
            # Related store info
            if "related_store" in sym:
                store = sym["related_store"]
                print(f"   Store Connection:")
                print(f"     Interface : {store['interface_name']}")
                print(f"     Implementation: {store['implementation_name']}")
                
            print("-" * 60)
            
    except Exception as e:
        print(f"Lookup error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
