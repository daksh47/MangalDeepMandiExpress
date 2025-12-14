import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import requests
import os
import json
import time

GITHUB_OWNER = 'daksh47'
GITHUB_REPO = 'MangalDeepMandiExpress'
VAR_NAME = 'ORDER_HIST'
TARGET_COLLECTION = 'Orders'

key_dict = json.loads(os.environ.get('ORDER_FIREBASE'))
cred = credentials.Certificate(key_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

webhook_url = os.environ.get('ORDER_DISCORD')
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
    mention = "@everyone" 

    if safety == -1:
        title_text = "🚨 CRITICAL: ORDER DELETED"
        color_code = 15548997 
        message_content = f"{mention} ⚠️ **STOP! ORDER DELETED!**" 
        desc_text = f"**{abs(diff)}** Order(s) have been REMOVED."
        repeat_count = 10  
        delay = 2         
    else:
        title_text = "💰 CHA-CHING! NEW ORDER"
        color_code = 5763719   
        message_content = f"{mention} 🚀 **WAKE UP! MONEY INCOMING!**"
        desc_text = f"**{diff}** New Order(s) just arrived."
        repeat_count = 5  
        delay = 2          

    payload = {
        "content": message_content,
        "allowed_mentions": {"parse": ["everyone"]},
        "embeds": [{
            "title": title_text,
            "description": desc_text,
            "color": color_code,
            "fields": [
                {"name": "📦 Total Orders Now", "value": f"**{new_count}**", "inline": True}
            ],
            "footer": {"text": "MangalDeep Notification System"}
        }]
    }
    
    print(f"Starting alert loop: {repeat_count} pings.")
    
    for i in range(repeat_count):
        try:
            requests.post(webhook_url, json=payload)
            if i < repeat_count - 1:
                time.sleep(delay)
        except Exception as e:
            print(f"Error sending alert {i+1}: {e}")

    print("Alert loop finished.")

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
