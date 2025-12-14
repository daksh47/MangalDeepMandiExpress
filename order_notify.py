import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import requests
import os
import json

GITHUB_OWNER = 'daksh47'
GITHUB_REPO = 'MangalDeepMandiExpress'
VAR_NAME = 'ORDER_HIST'
TARGET_COLLECTION = 'Orders'

key_dict = json.loads(os.environ.get('ORDER_FIREBASE'))
cred = credentials.Certificate(key_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

webhook_url = os.environ.get('ORDER_FIREBASE')
gh_token = os.environ.get('ORDER_STORE')

def get_last_count():
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/variables/{VAR_NAME}"
    headers = {
        "Authorization": f"Bearer {gh_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return int(resp.json().get('value', 0))
    return 0

def update_last_count(new_value):
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/variables/{VAR_NAME}"
    headers = {
        "Authorization": f"Bearer {gh_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    data = {"name": VAR_NAME, "value": str(new_value)}
    requests.patch(url, headers=headers, json=data)

def send_alert(new_count, diff, safety):
    payload = {
        "content": "🔔 **new order has been place**",
        "embeds": [{
            "title": "New Order Placed",
            "description": f"**{diff}** Order(s) Placed.",
            "color": 5763719,
            "fields": [{"name": "Total Orders", "value": str(new_count)}]
        }]
    }
    if safety == -1:
        payload = {
            "content": "🔔 **Order has been deleted**",
            "embeds": [{
                "title": "RED ALERTTTTTT",
                "description": f"**{abs(diff)}** Order(s) Deleted.",
                "color": 5763719,
                "fields": [{"name": "Total Orders", "value": str(new_count)}]
            }]
        }
        
    requests.post(webhook_url, json=payload)

def check_updates():
    last_count = get_last_count()
    
    results = db.collection(TARGET_COLLECTION).count().get()
    current_count = results[0][0].value
    
    diff = current_count - last_count
    if diff > 0:  
        send_alert(current_count, diff, 0)
    elif diff < 0:
        send_alert(current_count, diff, -1)
        
    update_last_count(current_count)

if __name__ == "__main__":
    check_updates()
