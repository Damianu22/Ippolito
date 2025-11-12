"""Test get_cliente_nome function."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.db import get_cliente_nome

def test_cliente_nome():
    """Test if get_cliente_nome returns correct client name."""
    
    app = create_app()
    
    with app.app_context():
        test_rifcontos = ["01040441", "01040958", "01044154"]
        
        print("Test get_cliente_nome:")
        print("-" * 80)
        
        for rifconto in test_rifcontos:
            nome = get_cliente_nome(rifconto)
            print(f"\nRifconto: {rifconto}")
            print(f"Nome: {nome}")

if __name__ == "__main__":
    test_cliente_nome()
