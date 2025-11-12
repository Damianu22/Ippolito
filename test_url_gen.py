"""Test direct URL generation for vista_ordini."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from flask import url_for

def test_url_generation():
    """Test if URL is generated correctly."""
    
    app = create_app()
    
    with app.app_context():
        # Test URL generation with a sample rifconto
        test_rifconto = "01040751"
        
        try:
            url = url_for('main.vista_ordini', rifconto=test_rifconto)
            print(f"URL generato per rifconto '{test_rifconto}':")
            print(f"  {url}")
            print(f"\nURL completo: http://127.0.0.1:5000{url}")
            
            # Test with different rifcontos
            print("\n" + "-" * 80)
            print("Test con vari rifconto:")
            
            test_rifcontos = ["01040751", "01040958", "01040897", "01040441"]
            for rf in test_rifcontos:
                url = url_for('main.vista_ordini', rifconto=rf)
                print(f"  {rf} -> {url}")
                
        except Exception as e:
            print(f"Errore nella generazione URL: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_url_generation()
