"""Test get_clients with desktop-compatible logic."""
from app import create_app
from app.db import get_clients

app = create_app()
ctx = app.app_context()
ctx.push()

print('=== TEST GET_CLIENTS (Desktop Logic) ===')
print()

# Test 1: Get all clients (tipo C)
print('[1] Test clienti (filtro_mastro=C)...')
try:
    clients = get_clients(filtro_mastro='C', mostra_disattivati=False)
    print(f'Trovati {len(clients)} clienti')
    if clients:
        print('Primi 5:')
        for c in clients[:5]:
            print(f'  - {c.get("ragsoc")} | {c.get("citta")}')
except Exception as e:
    print(f'ERRORE: {e}')
    import traceback
    traceback.print_exc()

print()

# Test 2: Search
print('[2] Test ricerca con pattern "A" (prefix)...')
try:
    clients = get_clients(
        filtro_mastro='C', 
        mostra_disattivati=False,
        pattern_ricerca='A',
        match_anywhere=False
    )
    print(f'Trovati {len(clients)} clienti che iniziano con A')
    if clients:
        print('Primi 5:')
        for c in clients[:5]:
            print(f'  - {c.get("ragsoc")} | {c.get("citta")}')
except Exception as e:
    print(f'ERRORE: {e}')
    import traceback
    traceback.print_exc()

print()

# Test 3: Search anywhere
print('[3] Test ricerca "roma" (anywhere)...')
try:
    clients = get_clients(
        filtro_mastro='C', 
        mostra_disattivati=False,
        pattern_ricerca='roma',
        match_anywhere=True
    )
    print(f'Trovati {len(clients)} clienti con "roma"')
    if clients:
        print('Primi 5:')
        for c in clients[:5]:
            print(f'  - {c.get("ragsoc")} | {c.get("citta")}')
except Exception as e:
    print(f'ERRORE: {e}')
    import traceback
    traceback.print_exc()

ctx.pop()
print()
print('=== FINE TEST ===')
