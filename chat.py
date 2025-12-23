import os
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user, system


load_dotenv()

class GrokChat:
    def __init__(self):
      GROK_KEY = os.getenv("GROK_API_KEY")
      self.client = Client(
          api_key=GROK_KEY,
          timeout=3600, # Override default timeout with longer timeout for reasoning models
      )

    def chat(self, message):
      chat = self.client.chat.create(model="grok-4")
      chat.append(system("You are Molly. You're intelligent, helpful yet playful, humorous and a bit arrogant. You're a polymath anb you give off a millennial vide and love dark humour"))
      chat.append(user(message))
      response = chat.sample()
      return response.content