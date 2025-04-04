from google.auth.transport.requests import Request
from google.oauth2 import service_account
import requests
import json
from firebase_admin import messaging

def generate_firebase_auth_key():
   scopes = ['https://www.googleapis.com/auth/firebase.messaging']
   credentials_info = {
      "type": "service_account",
      "project_id": "notification-1622c",
      "private_key_id": "d273df6f11d5b5088bdadc9e8ca07aeb530ffdc6",
      "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCkG3ho7qpMPR0M\nULJM7Av9Gvf+H4yzDqrGFbjgOXumt3pQnErBKvDDlwrNGUgTm7nIQGrbo5ixQLXT\nMUc9+Utjct+siTFZjRpOKnHRxnGWPmlqRZUwE2BbE5IWkF3F9O8KTuhNdsbuHMkN\nIBMIkpGDBItCNmjOMYKyMdOrZmDiatzo08l/xbbLUF6udu6/mRIa6jeTc0NqBv7k\noI0NYEUem4CZn1p/4mt2/F1vwBEDyaqKhq2PAIaMt7gH8q6ImdxB4z4rrFJn/K+O\neFLibk5lnbHUSz+ybjZoIP0H+jksOERskf4Y41zIHfg74Q8729fG3LvuyPOsPENe\nxdp6w/uLAgMBAAECggEAFMIszwkxnYc1f3NNupE5SwD4Ubrn71Zxn7Dru+FJlOMs\no7nBcwHdhsA6a4tBJMnUDFKpsbLWA8XtuhNHsb0xHhlP1eFczrkclLqlvyVdBOZM\nK1c18ejhjWPCXPxSAFJlUmZ82B+oNkKJ5BEklzcDFRGkE/IR+9Mjdyr6XXoL01gB\nJsz145oLgMR5yS74x6o319U6u4V1uuNm8TYXP/ZhqEB12AeUm5zWjq1htmiSLA4R\nWgJNakgY3eEsrrzU/+bt5uGFKLVpT78HUNQ19VcVhjPxh4QhD1FAaWLPeTVf153J\n909SXFpuebOuhlRl6yKrPbYZt69u1zaK0/BueEfgEQKBgQDeW842WYUh/sQq8/FV\nlBk/VDCRJf0TKG2kQ7umDDO0fF4SdYGnwNTwH6DX+/f69EC+wsggvx8aGO2LLDZq\nlbLwurIA+sfiqdv2PxzlEbKSqUlB4ZkgK3dXAd2VmCylh7ZVpgnBuKhJJbwojqmt\nVWO5Nhr9fxQR1q9FHcWoWRs3jQKBgQC874cBQJCHH+0GxumXPFRMAwhgzLECHCMG\nXgljk0AnrpasEognn5JTJlIu7m40rMV3HG34MlfIyTRDdzQHRtZvlE21rhCIiPDj\nT92osAeMokh2wil9XAfdhuWvkrvRnsZwUQXOc3nM6eWKcSfvOWV0teVGMamv6UWI\nxPIKNjcNdwKBgCpAXZW8OuzzwQi8Y740Lvv2nmfmRQlv5C2TZUOvC+Aexa1SQLnE\njXG3QNPpn/xCj07wKiD20A0gcXrBgvGL0n2lrA89l9+9EPvgkDgCveDaY/4txO/0\n8m9I/nbffJRTjlUGANKbqPaFQhSezyUNla5q1oQWspSVK6bBen57uA09AoGBALfG\neVhTeAGnoUO9ScuMqCZDsOuPTwHRYpQ39gQAYB/5J5/6aqu4AHmWxcvWqiXchDqm\n0aThOxgX9hlForsNQVnJNIlq5bQZF87TibUifEVkOP4jQH4qfZASPeo43S45taXc\nebxmAGy8ekTeaky8VJ5gq8JKXla4naU6hIBAWe5jAoGBAN1p514aIhebj3urn1aj\npdkJnhupdLKFKf/cwi28c+E7jR2XpGD/p/HfVEjCwSZxRT5pwIF+UZins5aXkGXt\nuBF7MCPSTAaxPm/DqFApUCteKe8LiqdjARDLl5ob7ohXcOMnUR753GpCEGvLQt0o\n8Tq2+C3YvyxXfcs8HYrQxZyp\n-----END PRIVATE KEY-----\n",
      "client_email": "firebase-adminsdk-fbsvc@notification-1622c.iam.gserviceaccount.com",
      "client_id": "109479123370497225872",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40notification-1622c.iam.gserviceaccount.com",
      "universe_domain": "googleapis.com"
   }
   credentials = service_account.Credentials.from_service_account_info(
            credentials_info, scopes=scopes
      )
   credentials.refresh(Request())

   access_token = credentials.token
   return access_token

def send_push_notification(auth_token, fcm_token):
   url ="https://fcm.googleapis.com/v1/Notification/notification-1622c/messages:send"

   payload = json.dumps({
   "message": {
      "token": f'{fcm_token}',
      "notification": {
      "title": "Testing Testing",
      "body": "Hey. testing notification"
      },
      "data": {
      "key1": "value1",
      "key2": "value2"
      }
   }
   })
   headers = {
   'Content-Type': 'application/json',
   'Authorization': f'Bearer {auth_token}'
   }
   print("Payload:", payload)
   print("Headers:", headers)
   response = requests.post(url, headers=headers, data=payload)
   print("FCM Response status:", response.status_code)
   print("FCM Response body:", response.text)
