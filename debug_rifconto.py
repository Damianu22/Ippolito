"""Debug Rifconto values in piacon."""
from app import create_app
from app.db import get_configured_connection

app = create_app()
ctx = app.app_context()
ctx.push()

print('=== DEBUG RIFCONTO VALUES ===')
print()

try:
    with get_configured_connection() as conn:
        cursor = conn.cursor()
        
        # Check distinct Rifconto values
        print('[1] Valori distinti di Rifconto in piacon:')
        cursor.execute("""
            SELECT DISTINCT Rifconto, COUNT(*) as count
            FROM piacon
            WHERE Rifconto IS NOT NULL
            GROUP BY Rifconto
            ORDER BY count DESC
        """)
        rifconti = cursor.fetchall()
        print(f'Trovati {len(rifconti)} valori distinti:')
        for rif, count in rifconti[:10]:
            print(f'  {repr(rif)} -> {count} record')
        
        print()
        
        # Check sample records
        print('[2] Sample records da piacon:')
        cursor.execute("""
            SELECT TOP 5 
                Ragsoc, 
                denominazione, 
                Rifconto, 
                codice,
                Citta,
                ISNULL(disattivato, 0) as disattivato
            FROM piacon
            WHERE Ragsoc > ' ' AND codice <> '0000'
        """)
        records = cursor.fetchall()
        for rec in records:
            print(f'  Ragsoc: {repr(rec[0])}')
            print(f'  Denominazione: {repr(rec[1])}')
            print(f'  Rifconto: {repr(rec[2])}')
            print(f'  Codice: {repr(rec[3])}')
            print(f'  Citta: {repr(rec[4])}')
            print(f'  Disattivato: {rec[5]}')
            print()
        
except Exception as e:
    print(f'ERRORE: {e}')
    import traceback
    traceback.print_exc()

ctx.pop()
