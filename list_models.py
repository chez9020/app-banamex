from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("No API KEY found")
    exit(1)

client = genai.Client(api_key=api_key)
try:
    for m in client.models.list():
        if 'veo' in m.name:
            print(m.name)
except Exception as e:
    print(e)
