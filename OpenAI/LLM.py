from openai import OpenAI
import time
import json


class LLM:
    def __init__(self,llm_key=""):
        self.client = OpenAI(base_url = 'https://api.openai-proxy.com/v1',api_key = llm_key)
        self.client_embedding = self.client
        self.deploy_embedding = 'text-embedding-ada-002'
        self.name = "GPT"
        self.thread = None
        self.model = "gpt-3.5-turbo-1106"
        
    
    def chat_sync(self, model, messages, temperature=1.0, log=False):
        if log:
            print(messages)
        response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature
                )
        return response.choices[0].message.content