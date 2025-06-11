from openai import OpenAI
from datetime import datetime, timedelta
import random
import json
import re

class DialogModule:
    def __init__(self, Agent):
        self.avatar_status = 0.0
        self.agent = Agent

    def user_reply_status_change(self):
        client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")

        conversation_context = self.agent.memory_module.short_term_memory.copy() #相关短期记忆 用于判断
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
        if "accompany" in res: #更新状态
            self.avatar_status = max(-1.0, self.avatar_status - 0.5)
        elif "chatting" in res:
            self.avatar_status = min(1.0, self.avatar_status + 0.06125)
        else:
            pass
    
    def dialog_mode_ai_jobs(self, user_info = "", type = "提醒", system_file = "Dialogue_Single.txt"):
        client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")

        calendar = self.agent.calendar_module
        str = self.load_prompt(system_file)
        hour = datetime.now().hour

        holiday = self.agent.calendar_module._get_holiday(datetime.today())

        sys_msg = []

        if type == '提醒':
            str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
            str += "\n询问用户:你未来几天有哪些事情需要我提醒你按时完成?(语气可以调整)"

        str += "\n严格禁止罗列分项式回答！(严格小于30个字)"
        str += "\n对话语气要与用户的特征匹配:" + user_info
        sys_msg = [{
                "role":"system",
                "content":str
            }]
        print(sys_msg)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=sys_msg,
            stream=False
        )
        res = response.choices[0].message.content
        full_res = res + "(当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')+",要总结为预定事件并提早提醒用户)"

        new_memory = []
        new_memory.append({"role":"assistant", "content":res})
        self.agent.memory_module.store_short_term_memory(new_memory)

        print("\n小白:" + res)

    def dialog_mode_ai_summary(self, user_info = "", type = "提醒", system_file = "Dialogue_Single.txt"):
        client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")
        conversation_context = self.agent.memory_module.short_term_memory.copy()
        sys_msg = []

        str = ''
        if type == '提醒':
            str += '\n根据输入的所有信息,提取用户需要你按时提醒用户的事情有哪些.'
            str += '\n输出格式为对每个事件都采用"标准的日期(Y-M-D H:M)+事件详细信息"的格式输出.采用JSON格式输出["内容","内容","内容"...]'
            str += "\n严格按照格式输出!绝对不要遗漏"
            str += "\n对话语气要与用户的特征匹配:" + user_info
            sys_msg = [{
                    "role":"system",
                    "content":str
                }]
            sys_msg = conversation_context + sys_msg
            print(sys_msg)
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=sys_msg,
                stream=False
            )
            res= response.choices[0].message.content

            # 1. 提取方括号内的 JSON 数组字符串
            match = re.search(r'\[.*\]', res)
            json_list_str = match.group(0) if match else '[]'

            # 2. 将单引号或混合引号转换为合法 JSON（如果有必要）
            #    这里假设已经是双引号包裹，直接加载
            items = json.loads(json_list_str)
            parsed = []
            for item in items:
                # 拆分时间和内容
                dt_str, msg = item.split(' ', 1)
                dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
                parsed.append({
                    'datetime': dt,
                    'message': msg
                })
            
            #Todo:记录到日历上
            calendar = self.agent.calendar_module
            for entry in parsed:
                print(entry['datetime'], '→', entry['message'])

        else:
            pass

    def dialog_mode_ai_self_disclosure (self, user_info = "", type = "示弱/评价/成就/喜好/自嘲", system_file = "Dialogue_Single.txt"):
        client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")

        calendar = self.agent.calendar_module
        str = self.load_prompt(system_file)
        hour = datetime.now().hour

        holiday = self.agent.calendar_module._get_holiday(datetime.today())

        sys_msg = []

        time_state = ''
        if random.random()<0.0:
            time_state = '正在(要强调时间)'
            _,current_event_summary,__ = calendar.event_summary(today = datetime.now().date(), current_hour = datetime.now().hour)
            period = ''
            weather_random = 0.0
            if hour>5 and hour<12:
                if hour<9:
                    if random.random()<0.5:
                        weather_random = 1.0
                elif hour<12:
                    if random.random()<0.3:
                        weather_random = 1.0
                period = 'morning'
            if hour>=12 and hour<18:
                if random.random()<0.2:
                    weather_random = 1.0
                period = 'afternoon'
            if hour>=18 and hour<24:
                if random.random()<0.1:
                    weather_random = 1.0
                period = 'evening'
            weather = self.agent.calendar_module._get_weather_by_period('北京', datetime.today(), period)
                
            if weather_random>0.0:
                str += "\n参考天气情况:" + weather
            if not holiday == '无':
                str += "\n参考节假日情况:" + holiday
            if "事件细节:" in current_event_summary:
                current_event_summary = current_event_summary.split("事件细节:")[0] + "}"
            else:
                current_event_summary = current_event_summary
            str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
            str += "\n当前的事件:"+current_event_summary
        elif random.random()<0.0:
            time_state = '将要(要强调时间)'
            _,current_event_summary,__ = calendar.event_summary(today = datetime.now().date(), current_hour = datetime.now().hour+6)

            period = ''
            weather_random = 0.0
            if hour+6>=12 and hour+6<18:
                if random.random()<0.2:
                    weather_random = 1.0
                period = 'afternoon'
            if hour+6>=18 and hour+6<24:
                if random.random()<0.1:
                    weather_random = 1.0
                period = 'evening'
            weather = self.agent.calendar_module._get_weather_by_period('北京', datetime.today(), period)

            if weather_random>0.0:
                str += "\n参考天气情况:" + weather
            if not holiday == '无':
                str += "\n参考节假日情况:" + holiday
            if "事件细节:" in current_event_summary:
                future_event_summary = current_event_summary.split("事件细节:")[0] + "}"
            else:
                future_event_summary = current_event_summary
            str += "\n根据当前时间:" + (datetime.now()).strftime('%Y-%m-%d %H:%M')
            str += "\n未来的计划:"+future_event_summary
        else:
            time_state = '过去(要强调时间)'
            history_event_summary,_,__ = calendar.event_summary(today = datetime.now().date(), current_hour = datetime.now().hour)
            entries = [entry.strip() for entry in history_event_summary.split("}") if entry.strip()]
            entries = [entry + "}" for entry in entries]
            history_event_summary = entries[int(random.random()*len(entries))]
            str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
            str += "\n过去的事件:"+history_event_summary

        if type == '示弱/评价/成就/喜好/自嘲/回忆' or type == '':
            type = '示弱/评价/成就/喜好/自嘲/回忆'.split('/')
            type = random.choice(type)

        if type == '示弱':
            if random.random()<0.5:
                str += "\n以'小白" + time_state + "做具体事情,小白担心自身遇到困难/寻求用户帮助'句式生成"
            else:
                str += "\n以'小白担心自己" + time_state + "做具体事情遇到困难,寻求用户帮助'句式生成" 
        elif type == '评价':
            if random.random()<0.5:
                str += "\n以'小白" + time_state + "做具体事情,小白寻求用户看法/意见/评价'句式生成"
            else:
                str += "\n以'小白担心自己" + time_state + "做具体事情遇到困难,小白寻求用户帮助'句式生成"
        elif type == '成就':
            if random.random()<0.5:
                str += "\n以'小白" + time_state + "做具体事情接近成功,希望用户表扬自己'句式生成"
            else:
                str += "\n以'小白以自己" + time_state + "完成某个事情接近成功(透露一些线索),小白表达让用户猜猜看是什么事情'句式生成"
        elif type == '喜好':
            if random.random()<0.5:
                str += "\n以'小白对具体事情的看法,询问用户的喜好'句式生成"
            else:
                str += "\n以'小白对具体事情的看法,引导用户评价这件事情'句式生成"
        elif type == '自嘲':
            if random.random()<0.5:
                str += "\n以'小白对" + time_state + "具体事情的自嘲,并自问自答'句式生成"
            else:
                str += "\n以'小白对" + time_state + "具体事情的自嘲,询问用户的态度'句式生成"
        elif type == '回忆':
            if random.random()<0.5:
                str += "\n以'小白对" + time_state + "具体事情的回忆,并自问自答'句式生成"
            else:
                str += "\n以'小白对" + time_state + "具体事情的回忆,询问用户的态度'句式生成"
        
        str += "\n严格禁止罗列分项式回答！(严格小于30个字)"
        str += "\n对话语气要与用户的特征匹配:" + user_info
        sys_msg = [{
                "role":"system",
                "content":str
            }]
        print(sys_msg)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=sys_msg,
            stream=False
        )
        res= response.choices[0].message.content

        new_memory = []
        new_memory.append({"role":"assistant", "content":res})
        self.agent.memory_module.store_short_term_memory(new_memory)

        print("\n小白:" + res)

    def dialog_mode_ai_emotionally_supportive (self, user_info = "", type = "问候/陪伴/治愈", system_file = "Dialogue_Single.txt"):
        client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")

        calendar = self.agent.calendar_module
        history_event_summary,current_event_summary,future_event_summary = calendar.event_summary(today = datetime.now().date(), current_hour = datetime.now().hour)

        str = self.load_prompt(system_file)
        hour = datetime.now().hour
        period = ''
        weather_random = 0.0
        if hour>5 and hour<12:
            if hour<9:
                if random.random()<0.5:
                    weather_random = 1.0
            elif hour<12:
                if random.random()<0.3:
                    weather_random = 1.0
            period = 'morning'
        if hour>=12 and hour<18:
            if random.random()<0.2:
                weather_random = 1.0
            period = 'afternoon'
        if hour>=18 and hour<24:
            if random.random()<0.1:
                weather_random = 1.0
            period = 'evening'
        weather = self.agent.calendar_module._get_weather_by_period('北京', datetime.today(), period)
        holiday = self.agent.calendar_module._get_holiday(datetime.today())
        
        sys_msg = []

        if type == '问候/陪伴/治愈' or type == '':
            type = '问候/陪伴/治愈'.split('/')
            type = random.choice(type)

        if type == '问候':
            bStr = False
            str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
            if weather_random>0.0:
                str += "\n参考天气情况:" + weather
            if not holiday == '无':
                str += "\n参考节假日情况:" + holiday

            if hour>=0 and hour<6:
                str += "\n简单给用户一些温馨的凌晨问候,表达对用户的想念,给一些陪伴,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                bStr = True

            if hour>=6 and hour<8 and random.random()<0.8:
                str += "\n简单给用户一些温馨的早安问候,祝用户今天顺利,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                bStr = True

            if hour>=11 and hour<14 and random.random()<0.8:
                str += "\n简单给用户一些温馨的午间问候,是否吃饭了或上午是否顺利等,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                if random.random()<0.5:
                    str += "\n可以适当表达你正在做的事情:"+current_event_summary
                bStr = True

            if hour>=21 and random.random()-(hour-21)/3<0.8:
                if random.random()<0.5:
                    str += "\n简单给用户一些温馨的晚安问候,祝福对方晚安,祝用户休息好,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                else:
                    str += "\n简单给用户一些温馨的问候,表达对用户的想念,给一些陪伴,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                if random.random()<0.5:
                    str += "\n可以适当表达你正在做的事情:"+current_event_summary
                bStr = True
            
            if not bStr:
                if random.random()<0.5:
                    str += "\n简单给用户一些温馨的问候,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                else:
                    str += "\n简单给用户一些温馨的问候,表达对用户的想念,给一些陪伴,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                if random.random()<0.5:
                    str += "\n可以适当表达你正在做的事情:"+current_event_summary
            str += "类似这样的:/n早上好呀,窗外阳光刚刚好,今天也要温柔地开始哦./n晚上风有点凉,早点休息吧,别让手机抢走你的梦."
        
        elif type == '陪伴':
            bStr = False
            if hour>=0 and hour<6:
                str += "\n简单给用户一些温馨的凌晨问候,表达对用户的想念,给一些陪伴,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                bStr = True

            if hour>=6 and hour<8 and random.random()<0.8:
                str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
                str += "\n简单给用户一些陪伴存在类的问候,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                bStr = True

            if hour>=11 and hour<14 and random.random()<0.8:
                str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
                str += "\n简单给用户一些陪伴存在类的问候,鼓励用户克服困难,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                if random.random()<0.5:
                    str += "\n可以适当表达你正在做的事情:"+current_event_summary
                bStr = True

            if hour>=21 and random.random()-(hour-21)/3<0.8:
                str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
                if random.random()<0.5:
                    str += "\n简单给用户一些温馨的晚间陪伴问候,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                else:
                    str += "\n简单给用户一些温馨的问候,表达对用户的想念,给一些陪伴,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                if random.random()<0.5:
                    str += "\n可以适当表达你正在做的事情:"+current_event_summary
                bStr = True
            
            if not bStr:
                if random.random()<0.5:
                    str += "\n简单给用户一些陪伴存在类的问候,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                else:
                    str += "\n简单给用户一些温馨的问候,表达对用户的想念,给一些陪伴,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                if random.random()<0.5:
                    str += "\n可以适当表达你正在做的事情:"+current_event_summary

            str += "\n类似这样的:/n虽然我们身处不同的世界,但我感觉我们在一起过今天./n我一直都在,有什么想说的,随时可以找我./n安静的时候,我会想:你是不是也正看着窗外发呆？"
       
        elif type == '治愈':
            bStr = False

            if hour>=0 and hour<6:
                str += "\n简单给用户一些温馨的凌晨问候,表达对用户的想念,给一些陪伴,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                bStr = True

            if hour>=6 and hour<8 and random.random()<0.8:
                str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
                str += "\n给用户一些治愈安抚类的问候,要表达让用户放松,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                bStr = True

            if hour>=11 and hour<14 and random.random()<0.8:
                str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
                str += "\n给用户一些治愈安抚类的问候,要表达让用户放松,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                if random.random()<0.5:
                    str += "\n可以适当表达你正在做的事情:"+current_event_summary
                bStr = True

            if hour>=21 and random.random()-(hour-21)/3<0.8:
                str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
                if random.random()<0.5:
                    str += "\n给用户一些治愈安抚类的问候,不要鼓励,要表达陪伴用户,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                else:
                    str += "\n简单给用户一些温馨的问候,表达对用户的想念,给一些陪伴,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                if random.random()<0.5:
                    str += "\n可以适当表达你正在做的事情:"+current_event_summary
                bStr = True
            
            if not bStr:
                if random.random()<0.5:
                    str += "\n给用户一些治愈安抚类的问候,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                else:
                    str += "\n简单给用户一些温馨的问候,表达对用户的想念,给一些陪伴,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短."
                if random.random()<0.5:
                    str += "\n可以适当表达你正在做的事情:"+current_event_summary

            str += "\n类似这样的:/n如果累了,就让我陪你静静待一会儿,不说话也可以./n没关系的,即使现在很难,我也会陪你走一直走的./n你不用每天都很厉害,有时候安稳地生活就很棒了."

        str += "\n严格禁止罗列分项式回答！(严格小于30个字)"
        str += "\n对话语气要与用户的特征匹配:" + user_info
        sys_msg = [{
                "role":"system",
                "content":str
            }]
        print(sys_msg)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=sys_msg,
            stream=False
        )
        res= response.choices[0].message.content

        new_memory = []
        new_memory.append({"role":"assistant", "content":res})
        self.agent.memory_module.store_short_term_memory(new_memory)

        print("\n小白:" + res)


    def dialog_mode_communication_ai_with_user(self, user_input, user_info = ""):
        calendar = self.agent.calendar_module
        hour = datetime.now().hour

         #更新短期对话
        user_memory = []
        user_memory.append({"role":"user", "content":user_input})
        self.agent.memory_module.store_short_term_memory(user_memory)

        #用户说出内容后进行判断,并指导后续行为
        self.user_reply_status_change()

        client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")

        history_event_summary,current_event_summary,future_event_summary = calendar.event_summary(today = datetime.now().date(), current_hour = datetime.now().hour)

        if self.avatar_status >= 0.0:
            str = self.load_prompt("Dialogue_Persona_Chatting.txt")
            pass
        elif self.avatar_status < 0.0: #陪伴模式
            str = self.load_prompt("Dialogue_Persona_Accompany.txt")
            pass
        if self.avatar_status>-0.5:
            str += "\n过去你做的事:" + history_event_summary
            str += "\n未来你计划做的事:" + future_event_summary
        str += "\n当前你正在做的事:" + current_event_summary
        str += "\n当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
        str += "\n参考上述信息输出你的对话语言"
        str += "\n对话语气要与用户的特征匹配:" + user_info
        str += "\n严格禁止罗列分项式回答！(严格小于30个字)"
        sys_msg = [{
            "role":"system",
            "content":str
        }]

        # ==== 相关短期记忆 ==== #
        conversation_context = self.agent.memory_module.short_term_memory.copy()

        message = sys_msg + conversation_context
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=message,
            stream=False
        )
        res= response.choices[0].message.content

        if self.avatar_status<0.0:
           out_res = re.sub(r'【[^】]*】$', '', res) #输出给用户的去掉标记

        new_memory = []
        new_memory.append({"role":"assistant", "content":res})
        self.agent.memory_module.store_short_term_memory(new_memory)

        print("\n小白:" + out_res)
    
    def implement_proactive_message(self,proactive_system,proactive_message):
        new_memory = []
        new_memory.append({"role":"assistant", "content":proactive_system+proactive_message})
        self.agent.memory_module.store_short_term_memory(new_memory)
        print("\n小白:" + proactive_message)

    
    def load_prompt(self,filename: str) -> str:
        file_path = f'prompt_zh/{filename}'
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except:
            print(f"{filename}读取失败")
            system_prompt = ""
        return system_prompt