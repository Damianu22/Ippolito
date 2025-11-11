"""Test OPERATORI table login."""

from app import create_app
from app.db import fetch_user_by_username, get_configured_connection

app = create_app()
ctx = app.app_context()
ctx.push()

print('=== TEST TABELLA OPERATORI ===')
print()

# Check OPERATORI table
print('[1] Verifica tabella OPERATORI...')
try:
    with get_configured_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM dbo.OPERATORI')
        count = cursor.fetchone()[0]
        print(f'Trovati {count} operatori')
        
        cursor.execute('SELECT TOP 5 Nome, PASSWORD2005 FROM dbo.OPERATORI WHERE PASSWORD2005 IS NOT NULL')
        print('Sample operatori (Nome | Password):')
        for row in cursor.fetchall():
            print(f'  {repr(row[0])} | {repr(row[1])}')
except Exception as e:
    print(f'ERRORE: {e}')
    import traceback
    traceback.print_exc()

print()

# Test fetch_user_by_username
print('[2] Test fetch_user_by_username...')
try:
    with get_configured_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT TOP 1 Nome FROM dbo.OPERATORI WHERE PASSWORD2005 IS NOT NULL')
        first_nome = cursor.fetchone()
        if first_nome:
            nome = first_nome[0]
            print(f'Cerca operatore: {repr(nome)}')
            user = fetch_user_by_username(nome)
            if user:
                print('Trovato:')
                for key, value in user.items():
                    print(f'  {key}: {repr(value)}')
            else:
                print('NON trovato')
        else:
            print('Nessun operatore con password nel DB')
except Exception as e:
    print(f'ERRORE: {e}')
    import traceback
    traceback.print_exc()

print()

# Test login simulation
print('[3] Test simulazione login...')
try:
    with get_configured_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT TOP 1 Nome, PASSWORD2005 FROM dbo.OPERATORI WHERE PASSWORD2005 IS NOT NULL')
        row = cursor.fetchone()
        if row:
            test_nome = row[0]
            test_pass = row[1]
            print(f'Test con: Nome={repr(test_nome)}, Password={repr(test_pass)}')
            
            user_record = fetch_user_by_username(test_nome)
            if user_record:
                db_password = user_record.get('Password')
                print(f'Password dal DB: {repr(db_password)}')
                print(f'Password match: {test_pass == db_password}')
                
                if test_pass == db_password:
                    print('✓ LOGIN RIUSCITO')
                else:
                    print('✗ LOGIN FALLITO')
            else:
                print('✗ Operatore non trovato')
        else:
            print('Nessun operatore con password per test')
except Exception as e:
    print(f'ERRORE: {e}')
    import traceback
    traceback.print_exc()

print()
print('=== FINE TEST ===')
ctx.pop()
