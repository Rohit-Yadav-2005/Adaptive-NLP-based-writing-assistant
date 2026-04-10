import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_flow():
    print("Testing Registration...")
    reg_resp = requests.post(f"{BASE_URL}/api/v2/auth/register", json={
        "email": "test@enterprise.com",
        "password": "password123",
        "full_name": "Test User"
    })
    print(reg_resp.json())
    token = reg_resp.json().get("access_token")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\nTesting Workspace List...")
    ws_resp = requests.get(f"{BASE_URL}/api/v2/workspaces", headers=headers)
    workspaces = ws_resp.json()
    print(workspaces)
    org_id = workspaces[0]['id']
    
    print("\nTesting Document Creation...")
    doc_resp = requests.post(f"{BASE_URL}/api/v2/documents", headers=headers, json={
        "title": "Enterprise Strategy",
        "content": "Our strategy is to be the best Writing Assistant.",
        "org_id": org_id
    })
    doc = doc_resp.json()
    print(doc)
    doc_id = doc['id']
    
    print("\nTesting Document History...")
    hist_resp = requests.get(f"{BASE_URL}/api/v2/documents/{doc_id}/history", headers=headers)
    print(hist_resp.json())

if __name__ == "__main__":
    test_flow()
