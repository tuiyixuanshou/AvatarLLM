from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from datetime import datetime

import memory

class respond_module:
    def __init__(self):
        self.Avatar_status = "chatting"
        self.memory_module = memory.Memory(20)
    
    def user_reply_status_change(self):
        client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")

        conversation_context = self.memory_module.short_term_memory.copy() #相关短期记忆 用于判断
        #conversation_summary = "\n".join(conversation_context)
        conversation_summary = ""
        conversation_summary = ",".join([f"{e['role']}:{e['content']}" for e in conversation_context])
        prompt = self.load_prompt("Responde_Status_Choose.txt")+conversation_summary
        msg = [{
            "role":"user",
            "content":prompt
        }]
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=msg,
            stream=False
        )
        res= response.choices[0].message.content
        print(f"chosen states:{res}")
        self.Avatar_status = res #更新状态


    def llm_reply(self,user_input, system_file = "Dialogue_Persona.txt"):
         #更新短期对话
        user_memory = []
        user_memory.append({"role":"user", "content":user_input})
        self.memory_module.store_short_term_memory(user_memory)

        #用户说出内容后进行判断，并指导后续行为
        self.user_reply_status_change()

        client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")
        
        # ==== 相关短期记忆 ==== #
        conversation_context = self.memory_module.short_term_memory.copy()

        # ==== 近期规划的相关记忆 ==== #
        recent_proactive_event = self.memory_module.recent_proactive_event.copy() #近期规划的相关记忆
        #event_summary = ",".join(recent_proactive_event)
        event_summary = ",".join(
            f"[{e['date']} {e['time_slot']}] {e['message']}" for e in recent_proactive_event
        )

        sys_msg = [{
            "role":"system",
            "content":self.load_prompt(system_file)+
            f"\n目前真实世界时间：{datetime.now().strftime("%Y-%m-%d %H:%M")+
            f"\n近期发生的事件，仅做参考用：{event_summary}"}"
        }]

        conversation_context.append({"role":"user","content":user_input}) #用户输入内容
        

        # ==== 加入回复状态 ==== #
        # style = self.load_prompt(f"Responde_{self.Avatar_status}.txt")
        # sys_style = [{
        #     "role":"user",
        #     "content":style
        # }]

        #message = sys_msg + conversation_context + sys_style

        message = sys_msg + conversation_context

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=message,
            stream=False
        )
        res= response.choices[0].message.content
        #print("\n小白：" + res)

        new_memory = []
        new_memory.append({"role":"assistant", "content":res})
        self.memory_module.store_short_term_memory(new_memory)

        print("\n小白：" + res)


    
    def implement_proactive_message(self,proactive_system,proactive_message):
        
        new_memory = []
        new_memory.append({"role":"assistant", "content":proactive_system+proactive_message})
        self.memory_module.store_short_term_memory(new_memory)

        print("\n小白：" + proactive_message)

    
    def load_prompt(self,filename: str) -> str:
        file_path = f'prompt_zh/{filename}'
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except:
            print(f"{filename}读取失败")
            system_prompt = ""
        return system_prompt