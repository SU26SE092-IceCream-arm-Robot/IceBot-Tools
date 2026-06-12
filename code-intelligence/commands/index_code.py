import sys
import argparse
from pathlib import Path

# Add project root to path to allow importing codeintel and toolcore
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))

from codeintel.indexer import run_indexing

def main():
    parser = argparse.ArgumentParser(description="IceBot Code Intelligence Indexer CLI")
    parser.add_argument("--rebuild", action="store_true", help="Force rebuild the index (ignores cached hashes)")
    parser.add_argument("--source", type=str, default=None, help="Index a specific repository key only")
    parser.add_argument("--dry-run", action="store_true", help="Scan and parse files, output stats, but do not write to SQLite database")
    
    args = parser.parse_args()
    
    try:
        dry_str = " (DRY RUN)" if args.dry_run else ""
        print(f"Starting code indexing{dry_str}...")
        
        stats = run_indexing(source_key=args.source, rebuild=args.rebuild, dry_run=args.dry_run)
        
        if "duration" not in stats:
            print(stats.get("message", "No indexing performed."))
            return
            
        print(f"\nIndex completed in {stats['duration']:.2f}s{dry_str}")
        print(f"  Files scanned: {stats['files_scanned']}")
        print(f"  Files indexed: {stats['files_indexed']}")
        print(f"  Files skipped: {stats['files_skipped']} (unchanged)")
        print(f"  Symbols: {stats['symbols']:,}")
        print(f"  Endpoints: {stats['endpoints']:,}")
        print(f"  GraphQL fields: {stats['graphql_fields']:,}")
        print(f"  Handlers: {stats['handlers']:,}")
        if args.dry_run:
            print("  Stores: not computed in dry-run")
        else:
            print(f"  Stores: {stats['stores']:,}")
        print(f"  Relationships: {stats['relationships']:,}")
        
    except Exception as e:
        print(f"\nIndexing failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
