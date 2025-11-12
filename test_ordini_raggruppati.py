"""Test raggruppamento ordini e articoli."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.db import get_ordini_cliente, get_articoli_ordine

def test_ordini_raggruppati():
    """Test if orders are grouped by numdoc."""
    
    app = create_app()
    
    with app.app_context():
        test_rifconto = "01040441"
        
        print("=" * 80)
        print("TEST 1: Ordini raggruppati per numdoc")
        print("=" * 80)
        
        ordini = get_ordini_cliente(codcf=test_rifconto)
        
        print(f"\nTrovati {len(ordini)} ordini unici (raggruppati per numdoc)\n")
        
        # Show first 5 orders with article count
        for i, ordine in enumerate(ordini[:5], 1):
            print(f"{i}. Ordine N° {ordine['numdoc']} (raw: {ordine['numdoc_raw']})")
            print(f"   Data: {ordine['datdoc']}")
            print(f"   Articoli: {ordine.get('num_articoli', 1)}")
            print()
        
        # Test getting articles for an order with multiple items
        ordine_multi = next((o for o in ordini if o.get('num_articoli', 1) > 1), None)
        
        if ordine_multi:
            print("=" * 80)
            print(f"TEST 2: Articoli per ordine {ordine_multi['numdoc']} (ha {ordine_multi['num_articoli']} articoli)")
            print("=" * 80)
            
            articoli = get_articoli_ordine(
                codcf=test_rifconto,
                numdoc_raw=str(ordine_multi['numdoc_raw'])
            )
            
            print(f"\nTrovati {len(articoli)} articoli per l'ordine\n")
            
            for i, art in enumerate(articoli, 1):
                print(f"{i}. Pratica: {art['pratica_numero']}")
                print(f"   Articolo: {art['desart'][:60]}...")
                print(f"   Codice: {art['codart']}")
                print()
        else:
            print("\nNessun ordine con articoli multipli trovato nei primi 5.")

if __name__ == "__main__":
    test_ordini_raggruppati()
