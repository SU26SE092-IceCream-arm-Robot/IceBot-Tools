import sys
import json
from pathlib import Path

# Add project root to path to allow importing codeintel and toolcore
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))

from codeintel.config import EXPORT_DIR, ensure_directories
from codeintel.queries import get_all_symbols, get_all_endpoints, get_all_relationships

def main():
    try:
        ensure_directories()
        
        print("Exporting database records to JSON files...")
        
        # 1. Export symbols
        symbols = get_all_symbols()
        sym_file = EXPORT_DIR / "symbol_index.json"
        with open(sym_file, "w", encoding="utf-8") as f:
            json.dump(symbols, f, indent=2)
            
        # 2. Export endpoints
        endpoints = get_all_endpoints()
        ep_file = EXPORT_DIR / "endpoint_map.json"
        with open(ep_file, "w", encoding="utf-8") as f:
            json.dump(endpoints, f, indent=2)
            
        # 3. Export relationships
        relationships = get_all_relationships()
        rel_file = EXPORT_DIR / "relationships.json"
        with open(rel_file, "w", encoding="utf-8") as f:
            json.dump(relationships, f, indent=2)
            
        print(f"\nExport completed successfully!")
        print(f"  Symbols written to:       {sym_file.relative_to(project_root.parent)}")
        print(f"  Endpoints written to:     {ep_file.relative_to(project_root.parent)}")
        print(f"  Relationships written to: {rel_file.relative_to(project_root.parent)}")
        
    except Exception as e:
        print(f"Export failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
