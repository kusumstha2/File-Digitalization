import os
import json
import requests
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2 import service_account

# Load .env file
load_dotenv()

def generate_firebase_auth_key():
    scopes = ['https://www.googleapis.com/auth/firebase.messaging']
    credentials_path = {
    "type": "service_account",
    "project_id": "notification-1622c",
    "private_key_id": "6e40b9a51871740853d88b940279827ed71bf6af",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC5OoZS4jVLiMh8\nbArw67zi1P4C3+aVanfcVSP2XF4nCVjG0SEcuWYjn2BF7ere24uuk+LElziERGR6\nEeNz/ouRttCAtaYSOxysx5tR0+GzBEJKIuevYPZqHWhgrajdjOAfRQgJaI774bFs\nzxkuSmBnSSJ1kDrRUrLLhvIMQ181S8wz/lmdvwYaUtN1hZrq13l8Pr3vP834a/bL\nbFHjN/IpkWafXvLdQRPMACeZQbKFgbfsHRedUQvsKuH9G/y5UvB9iCGCf/YwYxXm\nKC/4Nf96X13lPPkl3kGrQywF0NWTXNG02tytPwQ83htU24HmrwhpLMgR9zemJDEY\ngYsYKo7vAgMBAAECggEAEJav4PcRVCpz33DC/2tIB1M79ytGOKtzAJs/apjrIGPd\n54W4iXIGi7os98D5qpZ5nrDv5jCvhxOjoVW+IRfy4qHqGnIqOrJrPFjEDZgEO/Ft\ns7tcidW35oOruBIqxWy7GxHQ88bBch13CQpNya+E4rsnXZAFNH9LiUlp9AnfRPkq\n9lOXnq73EnLszDG6IWQlivGcbjJkwNR3IjsGWuEOQT23pe7As9WVzIds1+9bHrOk\n5oGRjGRZh76IgBWJizMdJuDzE5ddAVVP1Kh+XOP4ty1MsTS5c24r3a19mble1uOB\nnyMVXc7pONANF5hGbIiAAJsL7V5/9Rt26dYSZKJhAQKBgQDxu00kqqfkiX3BbZJY\nSF33QC+sQCRPs3DzRNq7mRAf6A8tTlqoifxqrliK3aM0hJN0lUlRFFu9xbHLde+s\nzUwH07tFrHE9aKu5lei6cvmdIWlvncae81vxsEWZCsUy/sQ+FfYbuB3rEXk5fujm\ndVdbRKTlYg83VPzNuW7ZtoarPwKBgQDEKW5q71BWbOvmc/NzHdbWImQemlbMo3zv\nOmhFbcW4zMrDVZ9kYeG5p/P38szEVw35nuPwuntiypWwlXLXghjr8wriJsl9qfS4\nz5gSiauQvAcXonjLl/LQzRrbl8LMyjqxDF6ROzHF5y4w8Ud78gd06pdjxiHO2AqZ\nsJ8+lLmgUQKBgQCsEE977wFs2jUqTs0hi/leulB0wn9WP/sBHhy39d6VZ4AOFrzP\nRNDoOsuJpPO7uTaggHbcgKpArYy9r2f3z3X0CFE/6dv9AxlhE4TB2n80yoibS2oK\n0Fy872TK5/CwOMoFC2rQFkEthpWMSHqNOC8DJxxcrmz4TMVZxklSLOs0zwKBgH7C\nfzXe+709mZtMJm+nQqMRij00Yw7OPvegeK0U6IYo4IYlmGCX1/PPEpqRbb0avE8o\nXAe9meoXG3AGwzV8PnqKjefiRKZN43RhwdWI3TMkLjkZppF52VEQmWB5y0nnDNJI\nOfwDkoBeibzazeTMXAEzbyzsZgByHzd9qQoZtXJhAoGAPMe3aXPHJIaWppTBCNSK\n2Nnt+ua5/lxRp5zT1OgVvVQcJVnXFDOHkGM7C5LtYjVHv5Hftnq/LKE6w+AG0nal\nr9acr566uxBP/WaVjoXcf/6bQUcDyXEbufbWrD67qT1AeNv/Y4/UeLIHkD1lw2Jd\n4aUw62rYw6lW6ztXaqUuRh0=\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@notification-1622c.iam.gserviceaccount.com",
    "client_id": "109479123370497225872",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40notification-1622c.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
  }
   # points to firebase_key.json

    credentials = service_account.Credentials.from_service_account_info(
        credentials_path, scopes=scopes
    )
    credentials.refresh(Request())
    access_token = credentials.token
    

    return access_token
   

def send_push_notification(auth_token, fcm_token):
    url = "https://fcm.googleapis.com/v1/projects/notification-1622c/messages:send"

    payload = json.dumps({
        "message": {
            "token": fcm_token,
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
