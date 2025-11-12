"""Test to check rendered HTML for client cards."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app import create_app

def test_rendered_html():
    """Check if HTML is rendered correctly with links."""
    
    app = create_app()
    
    with app.test_client() as client:
        # Login first
        response = client.post('/', data={
            'username': 'ADMIN',  # Replace with valid credentials
            'password': 'Ippopisa22'  # Replace with valid password
        }, follow_redirects=True)
        
        # Now get clients page
        response = client.get('/clienti')
        
        if response.status_code == 200:
            html = response.data.decode('utf-8')
            
            # Check if links are present
            if 'client-card-link' in html:
                print("✓ Trovato class='client-card-link' nell'HTML")
            else:
                print("✗ NON trovato class='client-card-link' nell'HTML")
            
            if '/clienti/' in html and '/ordini' in html:
                print("✓ Trovati link con pattern '/clienti/.../ordini'")
                
                # Extract first few links
                import re
                links = re.findall(r'href="(/clienti/[^"]+/ordini)"', html)
                if links:
                    print(f"\nPrimi 3 link trovati:")
                    for link in links[:3]:
                        print(f"  - {link}")
                else:
                    print("✗ Nessun link estratto con regex")
            else:
                print("✗ NON trovati link con pattern '/clienti/.../ordini'")
            
            # Check for rifconto in href
            if 'rifconto=' in html:
                print("\n⚠️  WARNING: Trovato 'rifconto=' nell'HTML (potrebbe essere un problema di encoding)")
            
            # Save HTML for inspection
            with open('debug_clienti.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"\n✓ HTML salvato in 'debug_clienti.html' per ispezione")
            
        else:
            print(f"✗ Errore HTTP {response.status_code}")
            print(f"Response: {response.data.decode('utf-8')[:500]}")

if __name__ == "__main__":
    test_rendered_html()
