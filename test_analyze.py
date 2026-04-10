import requests
res = requests.post('http://127.0.0.1:8000/api/v2/auth/register', json={'email': 'apicheck@example.com', 'password': 'pass', 'full_name': 'test'})
tok = res.json().get('access_token')
if not tok:
    res = requests.post('http://127.0.0.1:8000/api/v2/auth/login', data={'username': 'apicheck@example.com', 'password': 'pass'})
    tok = res.json()['access_token']
headers = {'Authorization': f'Bearer {tok}'}
res2 = requests.post('http://127.0.0.1:8000/api/v2/analyze', json={'text': 'this are bad', 'target_style': 'general'}, headers=headers)
print(res2.status_code)
print(res2.text)
