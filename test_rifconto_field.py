"""Quick test to check if rifconto is being passed correctly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.db import get_clients

def test_clients_rifconto():
    """Test if get_clients returns rifconto field."""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get first 5 clients
            clients = get_clients(
                filtro_mastro="01",
                mostra_disattivati=False,
                pattern_ricerca=None,
                match_anywhere=True
            )
            
            print(f"Trovati {len(clients)} clienti\n")
            print("Primi 5 clienti con Rifconto:")
            print("-" * 80)
            
            for i, client in enumerate(clients[:5], 1):
                print(f"\n{i}. {client.get('ragsoc', 'N/A')}")
                print(f"   Città: {client.get('citta', 'N/A')}")
                print(f"   Rifconto: {client.get('rifconto', 'MANCANTE!')}")
                
                # Check if rifconto is present
                if 'rifconto' not in client:
                    print("   ⚠️  ERRORE: Campo rifconto mancante!")
                elif not client.get('rifconto'):
                    print("   ⚠️  WARNING: Rifconto vuoto!")
                else:
                    print(f"   ✓ Rifconto presente e valido")
                    
        except Exception as e:
            print(f"Errore durante il test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_clients_rifconto()
