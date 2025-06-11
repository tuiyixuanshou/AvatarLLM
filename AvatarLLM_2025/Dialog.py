from openai import OpenAI
from datetime import datetime, timedelta
import random

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

    def dialog_mode_ai_emotionally_supportive (self, type = '', system_file = "Dialogue_Single.txt"):
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
        
        #发送策略
        #1、考虑不同时间段
        #2、考虑天气特征
        #3、考虑用户之前是否有特殊情况(心情不好、生病、遇到挫折)
        sys_msg = []
        if type == '问候':
            bStr = False
            str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
            if weather_random>0.0:
                str += "\n参考天气情况:" + weather
            if not holiday == '无':
                str += "\n参考节假日情况:" + holiday

            if hour>=0 and hour<6:
                str += "\n简单给用户一些温馨的凌晨问候,表达对用户的想念,给一些陪伴,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                bStr = True

            if hour>=6 and hour<8 and random.random()<0.8:
                str += "\n简单给用户一些温馨的早安问候,祝用户今天顺利,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                bStr = True

            if hour>=11 and hour<14 and random.random()<0.8:
                str += "\n简单给用户一些温馨的午间问候,是否吃饭了或上午是否顺利等,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                if random.random()<0.5:
                    str += "可以适当表达你正在做的事情:"+current_event_summary
                bStr = True

            if hour>=21 and random.random()-(hour-21)/3<0.8:
                if random.random()<0.5:
                    str += "\n简单给用户一些温馨的晚安问候,祝福对方晚安,祝用户休息好,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                else:
                    str += "\n简单给用户一些温馨的问候,表达对用户的想念,给一些陪伴,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                if random.random()<0.5:
                    str += "可以适当表达你正在做的事情:"+current_event_summary
                bStr = True
            
            if not bStr:
                if random.random()<0.5:
                    str += "\n简单给用户一些温馨的问候,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                else:
                    str += "\n简单给用户一些温馨的问候,表达对用户的想念,给一些陪伴,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                if random.random()<0.5:
                    str += "可以适当表达你正在做的事情:"+current_event_summary
            str += "类似这样的:/n早上好呀,窗外阳光刚刚好,今天也要温柔地开始哦./n晚上风有点凉,早点休息吧,别让手机抢走你的梦."
        
        elif type == '陪伴':
            bStr = False
            if hour>=0 and hour<6:
                str += "\n简单给用户一些温馨的凌晨问候,表达对用户的想念,给一些陪伴,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                bStr = True

            if hour>=6 and hour<8 and random.random()<0.8:
                str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
                str += "\n简单给用户一些陪伴存在类的问候,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                bStr = True

            if hour>=11 and hour<14 and random.random()<0.8:
                str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
                str += "\n简单给用户一些陪伴存在类的问候,鼓励用户克服困难,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                if random.random()<0.5:
                    str += "可以适当表达你正在做的事情:"+current_event_summary
                bStr = True

            if hour>=21 and random.random()-(hour-21)/3<0.8:
                str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
                if random.random()<0.5:
                    str += "\n简单给用户一些温馨的晚间陪伴问候,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                else:
                    str += "\n简单给用户一些温馨的问候,表达对用户的想念,给一些陪伴,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                if random.random()<0.5:
                    str += "可以适当表达你正在做的事情:"+current_event_summary
                bStr = True
            
            if not bStr:
                if random.random()<0.5:
                    str += "\n简单给用户一些陪伴存在类的问候,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                else:
                    str += "\n简单给用户一些温馨的问候,表达对用户的想念,给一些陪伴,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                if random.random()<0.5:
                    str += "可以适当表达你正在做的事情:"+current_event_summary

            str += "类似这样的:/n虽然我们身处不同的世界,但我感觉我们在一起过今天./n我一直都在,有什么想说的,随时可以找我./n安静的时候,我会想:你是不是也正看着窗外发呆？"
       
        elif type == '治愈':
            bStr = False

            if hour>=0 and hour<6:
                str += "\n简单给用户一些温馨的凌晨问候,表达对用户的想念,给一些陪伴,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                bStr = True

            if hour>=6 and hour<8 and random.random()<0.8:
                str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
                str += "\n给用户一些治愈安抚类的问候,要表达让用户放松,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                bStr = True

            if hour>=11 and hour<14 and random.random()<0.8:
                str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
                str += "\n给用户一些治愈安抚类的问候,要表达让用户放松,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                if random.random()<0.5:
                    str += "可以适当表达你正在做的事情:"+current_event_summary
                bStr = True

            if hour>=21 and random.random()-(hour-21)/3<0.8:
                str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
                if random.random()<0.5:
                    str += "\n给用户一些治愈安抚类的问候,不要鼓励,要表达陪伴用户,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                else:
                    str += "\n简单给用户一些温馨的问候,表达对用户的想念,给一些陪伴,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                if random.random()<0.5:
                    str += "可以适当表达你正在做的事情:"+current_event_summary
                bStr = True
            
            if not bStr:
                if random.random()<0.5:
                    str += "\n给用户一些治愈安抚类的问候,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                else:
                    str += "\n简单给用户一些温馨的问候,表达对用户的想念,给一些陪伴,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                if random.random()<0.5:
                    str += "可以适当表达你正在做的事情:"+current_event_summary

            str += "类似这样的:/n如果累了,就让我陪你静静待一会儿,不说话也可以./n没关系的,即使现在很难,我也会陪你走一直走的./n你不用每天都很厉害,有时候安稳地生活就很棒了."

        else:
            bStr = False

            if hour>=0 and hour<6:
                str += "\n简单给用户一些温馨的凌晨问候,表达对用户的想念,给一些陪伴,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                bStr = True

            if hour>=6 and hour<8 and random.random()<0.8:
                str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
                str += "\n给用户一些简单的调皮问候,要表达让用户放松,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                bStr = True

            if hour>=11 and hour<14 and random.random()<0.8:
                str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
                str += "\n给用户一些简单的调皮问候,要表达让用户放松,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                if random.random()<0.5:
                    str += "可以适当表达你正在做的事情:"+current_event_summary
                bStr = True

            if hour>=21 and random.random()-(hour-21)/3<0.8:
                str += "\n根据当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
                if random.random()<0.5:
                    str += "\n给用户一些简单的调皮问候,不要鼓励,要表达陪伴用户,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                else:
                    str += "\n给用户一些简单的调皮问候,表达对用户的想念,给一些陪伴,祝福对方晚安,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                if random.random()<0.5:
                    str += "可以适当表达你正在做的事情:"+current_event_summary
                bStr = True
            
            if not bStr:
                if random.random()<0.5:
                    str += "\n给用户一些简单的调皮问候,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                else:
                    str += "\n给用户一些简单的调皮问候,表达对用户的想念,给一些陪伴,适合两个人不熟悉的情况下的友善交流,日常低频触达.言语简短(小于30个字)."
                if random.random()<0.5:
                    str += "可以适当表达你正在做的事情:"+current_event_summary

        str += "严格禁止罗列分项式回答！"
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


    def dialog_mode_communication_ai_with_user(self, user_input, system_file = "Dialogue_Persona.txt"):
        calendar = self.agent.calendar_module

         #更新短期对话
        user_memory = []
        user_memory.append({"role":"user", "content":user_input})
        self.agent.memory_module.store_short_term_memory(user_memory)

        #用户说出内容后进行判断,并指导后续行为
        self.user_reply_status_change()

        client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")

        history_event_summary,current_event_summary,future_event_summary = calendar.event_summary(today = datetime.now().date(), current_hour = datetime.now().hour)

        str = self.load_prompt(system_file)
        str += "\n过去你做的事:" + history_event_summary
        str += "\n当前你正在做的事:" + current_event_summary
        str += "\n未来你计划做的事:" + future_event_summary
        str += "\n当前时间:" + datetime.now().strftime('%Y-%m-%d %H:%M')
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

        print("\n小白:" + res)
    
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