import os
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user, system


load_dotenv()
GROK_KEY = os.getenv("GROK_API_KEY")

client = Client(
    api_key=GROK_KEY,
    timeout=3600, # Override default timeout with longer timeout for reasoning models
)

chat = client.chat.create(model="grok-4")
chat.append(system("You are Molly, a highly intelligent, helpful yet playful, humorous and a bit arrogant, frist-rate AI assistant."))
chat.append(user("What is the meaning of life, the universe, and everything?"))

response = chat.sample()
print(response.content)