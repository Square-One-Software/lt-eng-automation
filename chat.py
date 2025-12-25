import os
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user, system 
from xai_sdk.tools import web_search 


load_dotenv()

class GrokChat:
    def __init__(self):
      GROK_KEY = os.getenv("GROK_API_KEY")
      if not GROK_KEY:
        raise ValueError("GROK_API_KEY environment variable not set")
      
      self.client = Client(
          api_key=GROK_KEY,
          timeout=3600, # Override default timeout with longer timeout for reasoning models
      )
      self.conversation = self.client.chat.create(model="grok-4-1-fast",  
            tools=[
              web_search(),
            ],
            temperature=0.8,
            max_tokens=10000,
            reasoning_effort="low",
            messages=[system("You are Molly, a witty and humorous assistant who responds with a touch of sarcasm. Keep your answers concise and entertaining. Don't start with 'Oh darling'")]
      )

    def send_message(self, message):
      self.conversation.append(user(message))
      response = self.conversation.sample()
      return response.content