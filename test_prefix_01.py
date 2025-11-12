"""Test with correct Rifconto prefix 01."""
from app import create_app
from app.db import get_clients

app = create_app()
ctx = app.app_context()
ctx.push()

print('Test with Rifconto prefix 01 (clienti)...')
clients = get_clients(filtro_mastro='01', mostra_disattivati=False)
print(f'Trovati {len(clients)} clienti')
print()
print('Primi 10:')
for i, c in enumerate(clients[:10]):
    ragsoc = c.get('ragsoc', '')
    citta = c.get('citta', '')
    print(f'{i+1}. {ragsoc} - {citta}')

ctx.pop()
