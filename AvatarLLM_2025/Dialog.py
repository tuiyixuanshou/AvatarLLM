from openai import OpenAI
from datetime import datetime

class DialogModule:
    def __init__(self, Agent):
        self.avatar_status = "chatting"
        self.agent = Agent

    def user_reply_status_change(self):
        client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")

        conversation_context = self.agent.memory_module.short_term_memory.copy() #相关短期记忆 用于判断
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
        self.avatar_status = res #更新状态


    def llm_reply(self, user_input, system_file = "Dialogue_Persona.txt"):
        calendar = self.agent.calendar_module.calendar

         #更新短期对话
        user_memory = []
        user_memory.append({"role":"user", "content":user_input})
        self.agent.memory_module.store_short_term_memory(user_memory)

        #用户说出内容后进行判断，并指导后续行为
        self.user_reply_status_change()

        client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")

        # ==== 过去事件的相关记忆==== #       
        current_event_summary = ''
        history_event_summary = ''

        #从日历中选择出过去的事件
        if not calendar == None:
            time_index_container = [0,0]
            reverse_time_slot = ["morning", "afternoon", "evening"]
            # 获取当前时间
            current_hour = datetime.now().hour
            today = datetime.now().date().isoformat()
            for idx, item in enumerate(calendar):
                if item['date'] == today:
                    time_index_container[0] = idx
                    break
            day_index = time_index_container[0]
            # 判断当前时间属于哪个时段
            if 6 <= current_hour < 12:
                time_slot = 0  # 早上
            elif 12 <= current_hour < 18:
                time_slot = 1  # 中午
            else:
                time_slot = 2  # 晚上

            for index in range(-2,1):
                _day_index = day_index + index
                if _day_index >= 0 and _day_index < len(calendar): 
                    for _time_slot in range(0,3):
                        if index == 0:
                            if _time_slot > time_slot:
                                break
                            if _time_slot == time_slot:
                                proactive_system = f"时间：{calendar[_day_index]['date']}{reverse_time_slot[_time_slot]},事件描述:{calendar[_day_index][reverse_time_slot[_time_slot]]['task_planning']}"
                                proactive_message = calendar[_day_index][reverse_time_slot[_time_slot]]['task_details']
                                if len(proactive_message)> 0:
                                    info = proactive_system + "事件细节:" + proactive_message
                                    current_event_summary += '{' + info + '}'
                        proactive_system = f"时间：{calendar[_day_index]['date']}{reverse_time_slot[_time_slot]},事件描述:{calendar[_day_index][reverse_time_slot[_time_slot]]['task_planning']}"
                        proactive_message = calendar[_day_index][reverse_time_slot[_time_slot]]['task_details']
                        if len(proactive_message)> 0:
                            info = proactive_system + "事件细节:" + proactive_message
                            history_event_summary += '{' + info + '}'

        # ==== 近期的规划 ==== #
        future_event_summary = ''

        #从日历中选择出对未来期待度最大的事件
        if not calendar == None:
            time_index_container = [0,0]
            reverse_time_slot = ["morning", "afternoon", "evening"]
            # 获取当前时间
            current_hour = datetime.now().hour
            today = datetime.now().date().isoformat()
            for idx, item in enumerate(calendar):
                if item['date'] == today:
                    time_index_container[0] = idx
                    break
            day_index = time_index_container[0]
            # 判断当前时间属于哪个时段
            if 6 <= current_hour < 12:
                time_slot = 0  # 早上
            elif 12 <= current_hour < 18:
                time_slot = 1  # 中午
            else:
                time_slot = 2  # 晚上

            for index in range(0,3):
                _day_index = day_index + index
                if _day_index >= 0 and _day_index < len(calendar): 
                    for _time_slot in range(0,3):
                        if index == 0:
                            if _time_slot <= time_slot:
                                break
                        value = float(calendar[_day_index][reverse_time_slot[_time_slot]]['task_planning_score'])
                        if value > 2.0:
                            proactive_system = f"时间：{calendar[_day_index]['date']}{reverse_time_slot[_time_slot]},事件描述:{calendar[_day_index][reverse_time_slot[_time_slot]]['task_planning']}"
                            if len(proactive_system)> 0:
                                info = proactive_system
                                future_event_summary += '{' + info + '}'
        if future_event_summary == '':
            future_event_summary = '还没想好（禁止编事情）'
        #recent_proactive_event = self.agent.memory_module.recent_proactive_event.copy() #近期规划的相关记忆
        #event_summary = ",".join(recent_proactive_event)
        #event_summary = ",".join(
        #    f"[{e['date']} {e['time_slot']}] {e['message']}" for e in recent_proactive_event
        #)

        str = self.load_prompt(system_file)
        str += "\n过去你做的事：" + history_event_summary
        str += "\n当前你正在做的事：" + current_event_summary
        str += "\n未来你计划做的事：" + future_event_summary
        str += "\n当前时间：" + datetime.now().strftime('%Y-%m-%d %H:%M')
        str += "\n参考上述信息回答用户的问题"
        sys_msg = [{
            "role":"system",
            "content":str
        }]

        # ==== 相关短期记忆 ==== #
        conversation_context = self.agent.memory_module.short_term_memory.copy()

        # ==== 加入回复状态 ==== #
        # style = self.load_prompt(f"Responde_{self.avatar_status}.txt")
        # sys_style = [{
        #     "role":"user",
        #     "content":style
        # }]
        #message = sys_msg + conversation_context + sys_style

        message = sys_msg + conversation_context
        print(message)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=message,
            stream=False
        )
        res= response.choices[0].message.content

        new_memory = []
        new_memory.append({"role":"assistant", "content":res})
        self.agent.memory_module.store_short_term_memory(new_memory)

        print("\n小白：" + res)
    
    def implement_proactive_message(self,proactive_system,proactive_message):
        new_memory = []
        new_memory.append({"role":"assistant", "content":proactive_system+proactive_message})
        self.agent.memory_module.store_short_term_memory(new_memory)
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