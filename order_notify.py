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
VAR_NAME_1 = 'NOTIFY_HIST'
TARGET_COLLECTION = 'Orders'
TARGET_COLLECTION_1 = 'Notify-Users'

key_dict = json.loads(os.environ.get('ORDER_FIREBASE'))
cred = credentials.Certificate(key_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

webhook_url = os.environ.get('ORDER_DISCORD')
webhook_url_1 = os.environ.get('NOTIFY_DISCORD')
gh_token = os.environ.get('ORDER_STORE')
gh_token_1 = os.environ.get('NOTIFY_STORE')

def get_last_count(what):
    if what == 0:
        url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/variables/{VAR_NAME}"
        headers = {
            "Authorization": f"Bearer {gh_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    else:
        url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/variables/{VAR_NAME_1}"
        headers = {
            "Authorization": f"Bearer {gh_token_1}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return int(resp.json().get('value', 0))
    return 0
    

def update_last_count(new_value, what):
    if what == 0:
        url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/variables/{VAR_NAME}"
        headers = {
            "Authorization": f"Bearer {gh_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        data = {"name": VAR_NAME, "value": str(new_value)}
    else:
        url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/variables/{VAR_NAME_1}"
        headers = {
            "Authorization": f"Bearer {gh_token_1}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        data = {"name": VAR_NAME_1, "value": str(new_value)}
        
    requests.patch(url, headers=headers, json=data)
        

def send_alert(new_count, diff, safety, what):
    dashboard_link = "https://mdme-backend.web.app/admin" 
    mention = "@everyone" 

    if what == 0:
        if safety == -1:
            title_text = "🚨 CRITICAL: ORDER DELETED"
            color_code = 15548997  
            message_content = f"{mention} ⚠️ **STOP! ORDER DELETED!**" 
            desc_text = f"**{abs(diff)}** Order(s) have been REMOVED.\n[👉 Click here to view Dashboard]({dashboard_link})"
        else:
            title_text = "💰 CHA-CHING! NEW ORDER"
            color_code = 5763719 
            message_content = f"{mention} 🚀 **MONEY INCOMING!**"
            desc_text = f"**{diff}** New Order(s) just arrived.\n[👉 Click here to view Dashboard]({dashboard_link})"
    
        payload = {
            "content": message_content,
            "allowed_mentions": {"parse": ["everyone"]}, 
            "embeds": [{
                "title": title_text,
                "url": dashboard_link, 
                "description": desc_text,
                "color": color_code,
                "fields": [
                    {"name": "📦 Total Orders Now", "value": f"**{new_count}**", "inline": True}
                ],
                "footer": {"text": "MangalDeep Notification System"}
            }]
        }
        
        try:
            requests.post(webhook_url, json=payload)
            print("Alert sent successfully NewOrder .")
        except Exception as e:
            print(f"Error sending alert: {e}")
    else:
        title_text = "💰 CHA-CHING! NEW REQUEST"
        color_code = 5763719 
        message_content = f"{mention} 🚀 **OUT-OF-STOCK WANTED!**"
        desc_text = f"**{diff}** New Request(s) just arrived.\n[👉 Click here to view Dashboard]({dashboard_link})"
    
        payload = {
            "content": message_content,
            "allowed_mentions": {"parse": ["everyone"]}, 
            "embeds": [{
                "title": title_text,
                "url": dashboard_link, 
                "description": desc_text,
                "color": color_code,
                "fields": [
                    {"name": "📦 Total Requests Now", "value": f"**{new_count}**", "inline": True}
                ],
                "footer": {"text": "MangalDeep Notification System"}
            }]
        }
        
        try:
            requests.post(webhook_url_1, json=payload)
            print("Alert sent successfully Oos.")
        except Exception as e:
            print(f"Error sending alert: {e}")
        

def check_updates(wh):
    last_count = get_last_count(wh)
    
    if wh == 0:
        results = db.collection(TARGET_COLLECTION).count().get()
    else:
        results = db.collection(TARGET_COLLECTION_1).count().get()
        
    current_count = results[0][0].value
    
    diff = current_count - last_count
    if diff > 0:  
        send_alert(current_count, diff, 0, wh)
    elif diff < 0:
        send_alert(current_count, diff, -1, wh)
        
    update_last_count(current_count, wh)

if __name__ == "__main__":
    check_updates(0)
    check_updates(1)
