import requests
import json
from threading import Thread

class LLM_Manager:
    def __init__(self,base_url,api_key,model_name,system_prompt=None):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.system_prompt = system_prompt

        self.dialogue_history = []
        self.is_ai_running = False  # 防止并发请求

        if system_prompt and not self.dialogue_history:
            self._add_system_message()


    def _add_system_message(self):
        self.dialogue_history.append({
            "role":"system",
            "content":self.system_prompt
        })
    
    
    #处理用户输入内容
    def user_input_send(self,user_text,callback=None,type = None):
        if self.is_ai_running:
            print("等等哦，我还在思考上一个问题~")
            if callback: callback(None, "系统繁忙")
            return
        
        self.is_ai_running = True
        self._add_user_message(user_text)
        #print("当前对话历史:",json.dumps(self.dialogue_history,indent = 2,ensure_ascii=False))
        Thread(target=self._async_call_wrapper,args=(callback,type)).start()
        
    def _add_user_message(self,text):
        self.dialogue_history.append({
            "role":"user",
            "content":text
        })

    #封装异步调用
    def _async_call_wrapper(self,callback,type = None):
        try:
            if type:
                response = self._call_api()
            else:
                response= self._call_api(type)
            print("LLM responde:\n"+ response)
            self._add_assistant_message(response)
            error = None
        except Exception as e:
            response = None
            error = str(e)
        finally:
            self.is_ai_running = False

        if callback:
            print("LLM_Manager异步调用Callback函数")
            callback(response,error)

    
    def _call_api(self,type=None):
        headers = {
            "Authorization":f"Bearer {self.api_key}",
            "Content-Type":"application/json"
        }
        if not type:
            payload = {
            "model":self.model_name,
            "messages":self.dialogue_history,
            "stream":False,
            "response_format":{"type":"json_object"}
            }
        else:
            payload = {
            "model":self.model_name,
            "messages":self.dialogue_history,
            "stream":False,
            }

        response = requests.post(self.base_url,headers=headers,json = payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def _add_assistant_message(self,text):
        self.dialogue_history.append({
            "role":"assistant",
            "content":text
        })
    
    