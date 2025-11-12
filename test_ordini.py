"""Test script to verify get_ordini_cliente function."""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.db import get_ordini_cliente

def test_ordini():
    """Test retrieving orders for a sample client."""
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Test with a sample Rifconto code (use '01' prefix which is for clienti)
        # Using a client that has orders
        test_rifconto = "01040441"  # Client with 197 orders
        
        print(f"Testing get_ordini_cliente with rifconto: {test_rifconto}")
        print("-" * 80)
        
        try:
            ordini = get_ordini_cliente(codcf=test_rifconto)
        
            print(f"Trovati {len(ordini)} ordini\n")
            
            if ordini:
                print("Primi 5 ordini:")
                for i, ordine in enumerate(ordini[:5], 1):
                    print(f"\n{i}. Ordine N° {ordine['numdoc']} (raw: {ordine.get('numdoc_raw', 'N/A')})")
                    print(f"   Data: {ordine['datdoc']}")
                    print(f"   Pratica: {ordine['pratica_numero']}")
                    print(f"   Articolo: {ordine['desart']}")
                    print(f"   Cod. Art: {ordine['codart']} (hidden)")
            else:
                print("Nessun ordine trovato per questo cliente.")
                print("\nProvando con una query generica per vedere se ci sono ordini...")
                
                # Try to find any client with orders
                from app.db import get_configured_connection
                with get_configured_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT TOP 1 codcf, COUNT(*) as num_ordini
                        FROM tabfat02
                        WHERE tipdoc = 'OC'
                        GROUP BY codcf
                        ORDER BY COUNT(*) DESC
                    """)
                    result = cursor.fetchone()
                    if result:
                        print(f"Cliente con più ordini: {result[0]} ({result[1]} ordini)")
                        print(f"\nRiesegui il test con rifconto: {result[0]}")
                    
        except Exception as e:
            print(f"Errore durante il test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_ordini()
