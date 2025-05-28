import json
from datetime import datetime, timedelta
import os
import re
from openai import OpenAI

import Avatar
import World_Plan

class AvatarCalendar:
    def __init__(self, agent:Avatar.VirtualAgent, External_Event:World_Plan.ExternalEventManager, days=30, path="M_file/Avatar_calendar.json"):
        self.agent = agent
        self.days = days
        self.path = path
        self.weekday_map = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
        self.calendar = []
        self.Len_calendar = 0
        self. _init_calendar()

        self.External_Event = External_Event #外部事件管理类

    def _empty_period(self):
        #日历数据结构
        return {
            #"state_vector": [], #avatar读取当前状态
            "status": "", #random_plan,world_plan,user_plan  world_plan给出权重，world_plan映射到state vector上
            "life_style_weight":[1.0,1.0,1.0,1.0,1.0],#第一个：生理性 第二个：工作性质 第三个：休闲性质 第四个：社交性质 第五个：情感性质
            "task": "", 
            "task_details": "" #具体行动描述
        }

    def _init_calendar(self):
        """生成基础日历结构"""
        if os.path.exists(self.path):
        # 文件存在，读取它
            with open(self.path, "r", encoding="utf-8") as f:
                self.calendar = json.load(f)
                self.Len_calendar = min(len(self.calendar), 7)
            print(f"📖 已读取已有日历: {self.path}")
        else:
            today = datetime.today()
            self.calendar = []
            for i in range(self.days):
                day = today + timedelta(days=i)
                self.calendar.append({
                    "date": day.strftime('%Y-%m-%d'),
                    "weekday": self.weekday_map[day.weekday()],
                    "morning": self._empty_period(),
                    "afternoon": self._empty_period(),
                    "evening": self._empty_period()
                })
            self.Len_calendar = min(len(self.calendar), 7)
            self.save_calendar(self.calendar)
            print(f"🆕 新建基础日历: {self.path}")

    def save_calendar(self,calendar):
        json_str = json.dumps(calendar, ensure_ascii=False, indent=2)
        json_str = re.sub(
            r'\[\s*((?:[^\[\]]|\n)+?)\s*\]',
            lambda m: '[' + ' '.join(m.group(1).replace('\n', '').split()) + ']',
            json_str
        )
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(json_str)

    #@staticmethod
    def get_calendar_from_file(self,calendar_path="M_file/Avatar_calendar.json"):
        with open(calendar_path, "r", encoding="utf-8") as f:
            calendar = json.load(f)
        return calendar
    
    def fill_task_details(self,calendar,day_index,time_slot):
        client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")
        dim_names = [
            "生理健康需求", "疼痛规避需求", "健康保护需求", "情绪反应需求",
            "风险规避需求", "目标坚持需求", "好奇探索需求", "规范遵循需求",
            "亲社会性需求", "社会形象需求", "角色责任需求", "群体归属需求"
        ]
        if len(agent.bps_state_vector) != len(dim_names):
            print(f"⚠️ 状态向量维度数（{len(agent.bps_state_vector)}）与名称数量不匹配（{len(dim_names)}）")
            return
        message = [{"role": "system", "content": self.load_prompt("Fill_Task_Detail.txt")}]
        message.append({
            "role": "user",
            "content": (
                f"时间：生成 {calendar[day_index]['date']} ({calendar[day_index]['weekday']}) [{time_slot}]"
                + f"事件及进展：{calendar[day_index][time_slot]['task']}"
                + f"外部事件：{calendar[day_index][time_slot]['world_plan']}"
                + f"人物状态：体力值--{str(agent.bio_energy)},情绪效价--{agent.emotion.current_mood_valence()},情绪唤醒--{agent.emotion.current_mood_arousal()}"
                + f"人物bps特质：{', '.join(f'{name}: {round(val, 3)}' for name, val in zip(dim_names, agent.bps_state_vector))}"
                + "只返回task_detail文字内容即可"
            )
        })

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=message,
            stream=False
        )

        return response.choices[0].message.content



    def fill_slot(self, day_index, time_slot):

        calendar = self.get_calendar_from_file()
        #print(calendar[day_index][time_slot]["status"])
        """为指定天和时段填充内容（如0, 'morning'）"""
        if not (0 <= day_index < self.days):
            print("❌ 天数超范围！")
            return
        if time_slot not in ['morning', 'afternoon', 'evening']:
            print("❌ 时段必须是 morning/afternoon/evening")
            return

        print(f"\n生成 {calendar[day_index]['date']} ({calendar[day_index]['weekday']}) [{time_slot}] 的计划")


        #===========外部事件处理===========
        if not calendar[day_index][time_slot]["world_plan"] == "":
            print("外部事件进入事件池")
            world_plan = calendar[day_index][time_slot]["world_plan"]
            print(world_plan)
            self.External_Event.External_event_to_Action(world_plan) #对外部事件进行动作映射

        #===========日程活动倾向影响===========
        life_style_weight = calendar[day_idx][time_slot]["life_style_weight"]
        result = self.agent.select_best_behavior(top_k=3, current_Time_slot=time_slot,life_style_weight = life_style_weight)
        if result[0]:
            best_behavior, score = result[0]
            print(f"🕒 {time_slot.upper()}: {best_behavior}")
            #calendar[day_index][time_slot]["state_vector"] = [round(x, 3) for x in self.agent.bps_state_vector.tolist()]
            calendar[day_index][time_slot]["task"] = best_behavior
            calendar[day_index][time_slot]["status"] = "random_plan"
        else:
            print(f"⚠️ {time_slot.upper()} 当前时段无可选行为")
            calendar[day_index][time_slot]["status"] = "random_plan"
        
        #===========生成具体活动细节===========
        calendar[day_index][time_slot]["task_details"] = self.fill_task_details(calendar,day_index,time_slot)
        print("💬 自述：" + calendar[day_index][time_slot]["task_details"])
        self.save_calendar(calendar)
        agent.print_state()
        
        #外部事件库根据时间流逝更新
        self.External_Event.Updata_External_Event()
        #print(f"✅ {calendar[day_index]['date']} {time_slot} 计划生成完成\n")

    def show(self, day_index=None):
        if day_index is None:
            for idx, day in enumerate(self.calendar):
                print(f"{idx}: {day['date']} {day['weekday']}")
        else:
            print(json.dumps(self.calendar[day_index], ensure_ascii=False, indent=2))
    
    def load_prompt(self,filename: str) -> str:
        file_path = f'prompt_zh/{filename}'
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except:
            print(f"{filename}读取失败")
            system_prompt = ""
        return system_prompt


if __name__ == "__main__":
    with open("M_file/Event_pool.json", "r", encoding="utf-8") as f:
        behavior_library = json.load(f)
    agent = Avatar.VirtualAgent(Avatar.personality2, Avatar.emotional1, behavior_library)
    externalManager = World_Plan.ExternalEventManager("M_file/External_Event.json")

    cal = AvatarCalendar(agent,externalManager)

    for day_idx in range(cal.Len_calendar):
        print(f"\n\n\n📅 Day {day_idx}-------------------------------------------------")
        for slot in ["morning", "afternoon", "evening"]:
            try:
                cal.fill_slot(day_idx, slot)

            except Exception as e:
                print(f"生成 Day {day_idx} {slot} 出错: {e}")
        agent.daily_update()

    # while True:
    #     cmd = input("输入天数0-6,空格,时段morning/afternoon/evening（如 0 morning）,'q'退出: ").strip()
    #     if cmd.lower() == "q":
    #         break
    #     elif " " in cmd:
    #         try:
    #             day_str, slot = cmd.split()
    #             day_idx = int(day_str)
    #             cal.fill_slot(day_idx, slot)
    #         except Exception as e:
    #             print(e)
    #             print("输入格式错误，应为: 0 morning")
    #     else:
    #         print("❗无效输入")