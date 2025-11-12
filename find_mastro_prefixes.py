"""Find mastro prefixes for clienti and fornitori."""
from app import create_app
from app.db import get_configured_connection

app = create_app()
ctx = app.app_context()
ctx.push()

print('=== FIND MASTRO PREFIXES ===')
print()

try:
    with get_configured_connection() as conn:
        cursor = conn.cursor()
        
        # Get records grouped by first 2 chars of Rifconto
        print('[1] Prefissi Rifconto (primi 2 caratteri):')
        cursor.execute("""
            SELECT 
                LEFT(Rifconto, 2) as Prefix,
                COUNT(*) as Count,
                MIN(Ragsoc) as SampleName
            FROM piacon
            WHERE Rifconto IS NOT NULL AND LEN(Rifconto) >= 2
            GROUP BY LEFT(Rifconto, 2)
            ORDER BY COUNT(*) DESC
        """)
        prefixes = cursor.fetchall()
        for prefix, count, sample in prefixes[:15]:
            print(f'  {repr(prefix)} -> {count:4d} records (es: {sample})')
        
        print()
        
        # Check if there's a tipo field
        print('[2] Checking for tipo/categoria field...')
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'piacon'
              AND (COLUMN_NAME LIKE '%tipo%' OR COLUMN_NAME LIKE '%categ%')
        """)
        tipo_cols = cursor.fetchall()
        if tipo_cols:
            print('Colonne tipo/categoria trovate:')
            for col in tipo_cols:
                print(f'  - {col[0]}')
        else:
            print('Nessuna colonna tipo/categoria trovata')
        
        print()
        
        # Sample with different prefixes
        print('[3] Sample records per prefisso:')
        for prefix in ['01', '02', '03', '04', '05']:
            cursor.execute(f"""
                SELECT TOP 2 Ragsoc, Rifconto, Citta
                FROM piacon
                WHERE Rifconto LIKE '{prefix}%'
                  AND Ragsoc > ' '
                  AND codice <> '0000'
            """)
            records = cursor.fetchall()
            if records:
                print(f'\n  Prefisso {prefix}:')
                for ragsoc, rifconto, citta in records:
                    print(f'    {ragsoc} ({rifconto}) - {citta}')
        
except Exception as e:
    print(f'ERRORE: {e}')
    import traceback
    traceback.print_exc()

ctx.pop()
