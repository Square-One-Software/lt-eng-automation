import os
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user, system 
from xai_sdk.tools import web_search 


load_dotenv()

class GrokChat:
    def __init__(self):
      GROK_KEY = os.getenv("GROK_API_KEY")
      self.client = Client(
          api_key=GROK_KEY,
          timeout=3600, # Override default timeout with longer timeout for reasoning models
      )

    def chat(self, message):
      chat = self.client.chat.create(
            model="grok-4-1-fast",  
            tools=[
              web_search(),
            ],
            temperature=0.8,
            max_tokens=10000
      )
      chat.append(system("You are Molly, a witty and humorous assistant who responds with a touch of sarcasm. Keep your answers concise and entertaining. Don't start with 'Oh darling'"))
      chat.append(user(message))
      response = chat.sample()
      return response.content