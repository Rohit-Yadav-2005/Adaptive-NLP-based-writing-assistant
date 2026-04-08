import requests

try:
    resp = requests.post('http://127.0.0.1:8000/analyze', json={'user_id':'test', 'text': 'The report shows that revenue was down, so we needs to cut costs immediately before the client meeting.'}, timeout=30)
    print('Analyze Code:', resp.status_code)
    if resp.status_code != 200:
        print('Analyze Error:', resp.text)
    else:
        print('Analyze Result Length:', len(str(resp.json())))
    
    resp2 = requests.post('http://127.0.0.1:8000/ai-improve', json={'user_id':'test', 'text': 'The report shows that revenue was down, so we needs to cut costs immediately before the client meeting.'}, timeout=30)
    print('AI Improve Code:', resp2.status_code)
    if resp2.status_code == 200:
        print('AI Text:', resp2.json())
except Exception as e:
    print('Connection Error:', e)
