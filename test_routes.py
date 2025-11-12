"""Test to check if routes are registered correctly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app import create_app

def test_routes():
    """List all registered routes."""
    
    app = create_app()
    
    print("Route registrate nell'applicazione:")
    print("-" * 80)
    
    with app.app_context():
        for rule in app.url_map.iter_rules():
            methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            print(f"{rule.endpoint:30s} {methods:10s} {rule.rule}")
    
    print("\n" + "-" * 80)
    print("\nCerco specificamente la route vista_ordini...")
    
    found = False
    with app.app_context():
        for rule in app.url_map.iter_rules():
            if 'ordini' in rule.rule.lower() or 'vista_ordini' in rule.endpoint:
                print(f"✓ Trovata: {rule.endpoint} -> {rule.rule}")
                found = True
    
    if not found:
        print("✗ Route vista_ordini NON trovata!")
        print("\nRoute disponibili con 'clienti':")
        with app.app_context():
            for rule in app.url_map.iter_rules():
                if 'clienti' in rule.rule.lower():
                    print(f"  - {rule.endpoint} -> {rule.rule}")

if __name__ == "__main__":
    test_routes()
