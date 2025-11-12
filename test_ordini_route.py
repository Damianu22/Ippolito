"""Test to verify vista_ordini route works with login."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app import create_app

def test_vista_ordini_with_login():
    """Test if vista_ordini route works when logged in."""
    
    app = create_app()
    
    with app.test_client() as client:
        # Login first
        print("1. Tentativo di login...")
        response = client.post('/', data={
            'username': 'ADMIN',
            'password': 'Ippopisa22'
        }, follow_redirects=False)
        
        if response.status_code == 302:
            print(f"   ✓ Login successful (redirect to {response.location})")
        else:
            print(f"   ✗ Login failed (status {response.status_code})")
            print("   Continuo comunque il test...")
        
        # Check if we have session
        with client.session_transaction() as sess:
            if 'user' in sess:
                print(f"   ✓ Session attiva per utente: {sess['user']}")
            else:
                print("   ✗ Nessuna sessione attiva")
                return
        
        # Now try to access vista_clienti
        print("\n2. Accesso a /clienti...")
        response = client.get('/clienti', follow_redirects=False)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✓ Vista clienti accessibile")
        else:
            print(f"   ✗ Errore: {response.status_code}")
        
        # Test route directly (will redirect if not logged in, 404 if route doesn't exist)
        test_rifconto = "01040441"
        print(f"\n3. Test esistenza route /clienti/{test_rifconto}/ordini...")
        response = client.get(f'/clienti/{test_rifconto}/ordini', follow_redirects=False)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 302:
            print(f"   ✓ Route esiste (redirect perché non loggato: {response.location})")
        elif response.status_code == 404:
            print("   ✗ Route NON esiste (404)")
        
        # Now try to access vista_ordini properly if logged in
        if response.status_code != 404:
            print(f"\n4. Accesso a /clienti/{test_rifconto}/ordini con sessione...")
            response = client.get(f'/clienti/{test_rifconto}/ordini', follow_redirects=False)
            print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✓ Vista ordini accessibile!")
            html = response.data.decode('utf-8')
            
            # Check if title is present
            if 'Ordini Cliente' in html:
                print("   ✓ Trovato titolo 'Ordini Cliente'")
            
            # Check if rifconto is displayed
            if test_rifconto in html:
                print(f"   ✓ Trovato rifconto '{test_rifconto}' nella pagina")
            
            # Check if orders are present
            if 'order-card' in html:
                print("   ✓ Trovate card ordini")
            
            # Count orders
            order_count = html.count('order-card')
            print(f"   Numero card ordini trovate: {order_count}")
            
        elif response.status_code == 404:
            print("   ✗ Errore 404 - Route non trovata!")
            print(f"   Debug: {response.data.decode('utf-8')[:200]}")
        elif response.status_code == 302:
            print(f"   ✗ Redirect a: {response.location}")
        else:
            print(f"   ✗ Errore: {response.status_code}")
            print(f"   Response: {response.data.decode('utf-8')[:200]}")

if __name__ == "__main__":
    test_vista_ordini_with_login()
