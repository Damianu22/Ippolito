"""Quick test of login with DAMIANO."""
from app import create_app

app = create_app()
client = app.test_client()

print('Testing login with DAMIANO/123...')
response = client.post('/', data={
    'username': 'DAMIANO',
    'password': '123'
}, follow_redirects=False)

print(f'Status: {response.status_code}')
print(f'Location: {response.headers.get("Location")}')

if response.status_code == 302 and '/dashboard' in str(response.headers.get('Location', '')):
    print('✓ LOGIN SUCCESSFUL')
else:
    print('✗ LOGIN FAILED')
