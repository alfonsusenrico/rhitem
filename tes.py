import os
from apiclient.discovery import build
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv('api_key')

youtube = build('youtube','v3',developerKey = API_KEY)

request = youtube.search().list(q='Permission to dance',part='snippet',type='video',maxResults=10)


res = request.execute()
from pprint import PrettyPrinter
pp = PrettyPrinter()
for item in res['items']:
    pp.pprint(item['snippet']['title'])
    pp.pprint(item['id']['videoId'])
