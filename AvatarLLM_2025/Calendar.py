import json
import os
import re
import time as time_module
import requests
import random
import threading
import statistics
import chinese_calendar as chinese_calendar
from lunarcalendar import Converter, Solar, Lunar
from datetime import datetime, timedelta, time
from openai import OpenAI

class Calendar:
    def __init__(self, agent, days=7, path="M_file/Avatar_calendar.json"):
        self.agent = agent
        self.days = days
        self.path = path
        self.weekday_map = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
        self.calendar = []
        self._init_calendar()

    def _empty_period(self):
        #日历数据结构
        return {
            #"state_vector": [], #avatar读取当前状态
            "status": "", #random_plan,world_plan,user_plan  world_plan给出权重，world_plan映射到state vector上
            "world_plan":"",
            "weather": "天气情况：晴天;最高气温：20℃;最大风速：3km/h;空气湿度体感：舒适",
            "life_style_weight":[1.0,1.0,1.0,1.0,1.0],#第一个：生理性 第二个：工作性质 第三个：休闲性质 第四个：社交性质 第五个：情感性质
            "task_planning":"",         # 当前计划做的事件
            "task_planning_score":"",   # 当前计划做的事件的权重
            "task_future":"",           # 未来可能要做的事件
            "task_future_score":"",     # 未来可能要做的事件的权重
            "task_actual":"",           # 当前实际执行的事件
            "task_details": ""          # 当前实际执行的事件的具体行动描述
        }
    
    def _fill_period(self, city: str, date, period: str):
        #日历数据结构
        weather = self._get_weather_by_period(city, date, period)
        holiday = self._get_holiday(date)
        print("地点:" + city)
        print("节假日:" + holiday)
        print("日期:" + date.strftime('%Y-%m-%d'))
        print("时间段:" + period)
        print("天气:" + weather)
        return {
            #"state_vector": [], #avatar读取当前状态
            "status": "", #random_plan,world_plan,user_plan,role_play  world_plan给出权重，world_plan映射到state vector上
            "world_plan":"",
            "weather": weather,
            "holiday": holiday,
            "life_style_weight":[1.0,1.0,1.0,1.0,1.0],#第一个：生理性 第二个：工作性质 第三个：休闲性质 第四个：社交性质 第五个：情感性质
            "task_planning":"",         # 当前计划做的事件
            "task_planning_score":"",   # 当前计划做的事件的权重
            "task_future":"",           # 未来可能要做的事件
            "task_future_score":"",     # 未来可能要做的事件的权重
            "task_actual":"",           # 当前实际执行的事件
            "task_details": ""          # 当前实际执行的事件的具体行动描述
        }
    
    def _solar_to_lunar(self, date: datetime.date) -> str:
        """
        将 datetime.date 类型的公历日期转换为农历字符串。
        """
        solar = Solar(year=date.year, month=date.month, day=date.day)
        lunar = Converter.Solar2Lunar(solar)

        # 输出格式示例：农历 2025年四月三十
        day_name = str(lunar.day)+"号"
        month_name = str(lunar.month)
        if lunar.day == 1:
            day_name = "初一"
        if lunar.day == 2:
            day_name = "初二"
        if lunar.day == 3:
            day_name = "初三"
        if lunar.day == 4:
            day_name = "初四" 
        if lunar.day == 5:
            day_name = "初五" 
        if lunar.day == 15:
            day_name = "十五" 
        if lunar.month == 1:
            month_name = "正"
        if lunar.month == 12:
            month_name = "腊"
        return f"农历{month_name}月{day_name}"

    def _get_holiday(self, date):
        # 判断是否为节假日
        is_holiday = chinese_calendar.is_holiday(date)

        # 获取节日详情
        on_holiday, holiday_name = chinese_calendar.get_holiday_detail(date)

        on_workday = chinese_calendar.is_workday(date)	# 是否为工作日（含补班日）
        in_lieu = chinese_calendar.is_in_lieu(date)	# 是否为调休日（周末但补班）
        lunar = self._solar_to_lunar(date)

        if in_lieu:
            return "调休,周末但补班"
        if on_holiday:
            return holiday_name + "(" + lunar + ")"
        if not on_workday:
            return "周末"
        return "无"

    def _get_weather_by_period(self, city: str, date, period: str):
        date = date.strftime('%Y-%m-%d')
        city_coords = {
            "北京": (39.9042, 116.4074),
            "上海": (31.2304, 121.4737),
            "杭州": (30.2741, 120.1551),
            "成都": (30.5728, 104.0668),
            "南京": (32.0603, 118.7969),
            "深圳": (22.5431, 114.0579),
            "洛杉矶": (34.0522, -118.2437)
        }

        if city not in city_coords:
            return "城市暂不支持"

        def determine_time_range(period: str):
            """根据时段名称返回小时范围"""
            if period == "morning":
                return range(6, 12)
            elif period == "afternoon":
                return range(12, 18)
            elif period == "evening":
                return range(18, 24)
            else:
                return None  # 支持未来扩展更多时段名
    
        hours = determine_time_range(period)
        if not hours:
            return "不支持的时段名，请使用 '上午'、'下午' 或 '晚上'"

        lat, lon = city_coords[city]

        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&hourly=temperature_2m,weathercode,precipitation_probability,"
            f"relative_humidity_2m,windspeed_10m"
            f"&timezone=auto&start_date={date}&end_date={date}"
        )

        response = requests.get(url)
        if response.status_code != 200:
            return "天气数据获取失败"

        data = response.json()
        hourly = data["hourly"]
        times = hourly["time"]

        temps, winds, humidities, rain_probs, codes = [], [], [], [], []

        for i, t in enumerate(times):
            hour = int(t[-5:-3])
            if hour in hours:
                temps.append(hourly["temperature_2m"][i])
                winds.append(hourly["windspeed_10m"][i])
                humidities.append(hourly["relative_humidity_2m"][i])
                rain_probs.append(hourly["precipitation_probability"][i])
                codes.append(hourly["weathercode"][i])

        if not temps:
            return f"{date} {period} 时段无天气数据"

        median_temp = round(statistics.median(temps), 1)
        median_wind = round(statistics.median(winds), 1)
        median_humidity = round(statistics.median(humidities), 1)
        median_rain_prob = round(statistics.median(rain_probs), 1)
        code = max(set(codes), key=codes.count)

        weather_map = {
            0: "晴", 1: "晴", 2: "多云", 3: "阴天", 45: "薄雾", 48: "霜雾",
            51: "轻微毛毛雨", 53: "中等毛毛雨", 55: "密集毛毛雨",
            61: "小雨", 63: "中雨", 65: "大雨", 66: "轻微冻雨", 67: "强冻雨",
            71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒",
            80: "局部小阵雨", 81: "中等阵雨", 82: "强阵雨",
            85: "局部小阵雪", 86: "局部大阵雪",
            95: "雷暴", 96: "雷暴夹冰雹", 99: "强雷暴夹冰雹"
        }

        def humidity_feel(h):
            if h <= 30:
                return "非常干燥"
            elif h <= 50:
                return "干爽"
            elif h <= 70:
                return "舒适"
            elif h <= 85:
                return "潮湿"
            else:
                return "非常潮湿"
        median_humidity = humidity_feel(median_humidity)

        precip_prob = pow(median_rain_prob / 100.0, 0.5)
        r = random.random()

        if r < precip_prob:
            # 下雨了
            weather = weather_map.get(max(51,code), "晴天") 
            return (f"天气:{weather}" + f";气温:{median_temp}℃" + f";风速:{median_wind} km/h" + f";空气湿度体感:{median_humidity}")
        else:
            # 没下雨
            weather = weather_map.get(min(3,code), "晴天") 
            return (f"天气:{weather}" + f";气温:{median_temp}℃" + f";风速:{median_wind} km/h" + f";空气湿度体感:{median_humidity}")

       
    def _init_calendar(self):
        """生成基础日历结构"""
        if os.path.exists(self.path):
        # 文件存在，读取它
            with open(self.path, "r", encoding="utf-8") as f:
                self.calendar = json.load(f)
            print(f"📖 已读取已有日历: {self.path}")
        else:
            today = datetime.today()
            self.calendar = []
            location = "北京"
            for i in range(self.days):
                day = today + timedelta(days=i)
                self.calendar.append({
                    "date": day.strftime('%Y-%m-%d'),
                    "location": location,
                    "weekday": self.weekday_map[day.weekday()],
                    "morning": self._fill_period(location,day,"morning"),
                    "afternoon": self._fill_period(location,day,"afternoon"),
                    "evening": self._fill_period(location,day,"evening"),
                })
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

    def get_calendar_from_file(self,calendar_path="M_file/Avatar_calendar.json"):
        with open(calendar_path, "r", encoding="utf-8") as f:
            calendar = json.load(f)
        return calendar
    
    def task_details_expand_user_favorite(self, prompt_file, input_info, user_favorite):
        client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")
        message = [{"role": "system", "content": "判断基础内容中是否涉及了“聊天/娱乐”。根据上述判断，输出“Yes”，或“No”"}]
        message.append({
                "role": "system",
                "content": "基本信息:" + input_info
            })
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=message,
            stream=False
        )
        if 'Yes' in response.choices[0].message.content:
            message = [{"role": "system", "content": self.load_prompt(prompt_file)}]
            msg = "基本信息:" + input_info + ";我的喜好:" + user_favorite
            message.append({
                "role": "system",
                "content": msg
            })
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=message,
                stream=False
            )
            return response.choices[0].message.content.replace('\n', '').replace('\r', '')
        return input_info.replace('\n', '').replace('\r', '')

    def task_details_expand(self, calendar, day_index, time_slot, prompt_file, input_info, holidayInfo = True, weatherInfo = True, friends = []):
        task_info = ''
        if holidayInfo:
            task_info += f"节假日：{calendar[day_index][time_slot].get('holiday', '')}\n"
        if weatherInfo:
            task_info += f"天气：{calendar[day_index][time_slot].get('weather', '')}\n"
        task_info += f"现在时间：生成 {calendar[day_index]['date']} ({calendar[day_index]['weekday']}) [{time_slot}(生成的内容在逻辑上要符合时间特点)]"
        task_info += "基本信息:" + input_info

        client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")
        message = [{"role": "system", "content": self.load_prompt(prompt_file)}]
        message.append({
                "role": "system",
                "content": task_info
            })
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=message,
            stream=False
        )
        return response.choices[0].message.content.replace('\n', '').replace('\r', '')
    
    def fill_task_details(self, calendar, day_index, time_slot, prompt_file, task_planning = None, gender = "男", bio_energy = 1.0, task_planning_score = 0.5, task_future = None, task_future_score = 0.5, task_actual = None, holidayInfo = True, weatherInfo = True, friends = []):
        client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")

        message = [{"role": "user", "content": self.load_prompt(prompt_file)}]
        task_info = ""
        task_info += f"外部事件：{calendar[day_index][time_slot].get('world_plan', '')}\n"

        task_expect = ""
        if task_planning_score < 0.7:
            task_expect = "(一般期待)"
        elif task_planning_score < 0.8:
            task_expect = "(比较期待)"
        elif task_planning_score < 0.9:
            task_expect = "(很期待)"
        elif task_planning_score < 1.1:
            task_expect = "(非常期待)"
        else:
            task_expect = "(超级期待)"

        future_task_expect = ""
        if task_future_score < 0.7:
            future_task_expect = "(一般期待这件事)"
        elif task_future_score < 1.0:
            future_task_expect = "(比较期待这件事)"
        elif task_future_score < 1.3:
            future_task_expect = "(很期待这件事)"
        elif task_future_score < 1.6:
            future_task_expect = "(非常期待这件事)"
        else:
            future_task_expect = "(超级期待这件事)"

        task = ''
        if not task_planning == None:
            task = f"计划执行的事件：【{task_planning}{task_expect}】\n"
        if not task_actual == None:
            task = f"原计划执行：{task_planning},实际执行的是：【{task_actual}{task_expect}】\n"
        if not task_future == None:
            task += f"输出的内容中要包含计划未来执行的事件：【{task_future}{future_task_expect}】\n"
        if len(friends) > 0:
            task += f"你的伙伴包括:"
            for item in friends:
                task += item
            task += f"根据事件的内容，选择最合适的伙伴加入到叙事内容里。\n"
        task_info += task

        if holidayInfo:
            task_info += f"节假日：{calendar[day_index][time_slot].get('holiday', '')}\n"
        if weatherInfo:
            task_info += f"天气：{calendar[day_index][time_slot].get('weather', '')}\n"
        
        msg = (f"现在时间：生成 {calendar[day_index]['date']} ({calendar[day_index]['weekday']}) [{time_slot}(生成的内容在逻辑上要符合时间特点)]"
                + task_info
                + f"人物状态：性别---{gender},体力--{str(bio_energy)}"
                + "只返回task_detail文字内容即可")
        message.append({
            "role": "system",
            "content": msg
        })
        
        #print(message)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=message,
            stream=False
        )

        rp = ['\n','\r',' ','任务详情','task_details',':','：','任务完成']
        for item in rp:
           response.choices[0].message.content = response.choices[0].message.content.replace(item,'') 
        return response.choices[0].message.content

    def prepare_calendar(self, day_index, time_slot):
        #calendar = self.get_calendar_from_file()
        if not (0 <= day_index < self.days):
            print("❌ 天数超范围！")
            return
        if time_slot not in ['morning', 'afternoon', 'evening']:
            print("❌ 时段必须是 morning/afternoon/evening")
            return
        
        print(self.calendar[day_index]['location'] + "," + self.calendar[day_index][time_slot]['weather'] + ",节假日:" + self.calendar[day_index][time_slot]['holiday'])

        status = self.calendar[day_index][time_slot]["status"]

        # ==== life_style_weight权重生成 ====#
        matched_ranges = self.agent.external_event_manager.get_matching_social_phases_macro(self.calendar[day_index]["date"],self.calendar[day_index]["weekday"])
        keys = ["生理", "工作", "休闲", "社交", "情感"]
        life_style_weight = [1.0,1.0,1.0,1.0,1.0]
        for idx, influence_range in enumerate(matched_ranges):
            for i, key in enumerate(keys):
                low, high = influence_range[key]
                delta = random.uniform(low, high)
                life_style_weight[i] += delta
        self.calendar[day_index][time_slot]["life_style_weight"] = [round(w, 3) for w in life_style_weight]

        print(f"🚩{self.calendar[day_index]['date']}{time_slot}的life_style_weights:生理🍔 {self.calendar[day_index][time_slot]['life_style_weight'][0]},工作✍  {self.calendar[day_index][time_slot]['life_style_weight'][1]},休闲⚽ {self.calendar[day_index][time_slot]['life_style_weight'][2]},社交🗯  {self.calendar[day_index][time_slot]['life_style_weight'][3]},情感💕 {self.calendar[day_index][time_slot]['life_style_weight'][4]}")


        # ==== 外部事件响应 ====#
        if status == "" or status == "random_plan":
            # ===========外部事件处理=========== #
            if not self.calendar[day_index][time_slot]["world_plan"] == "":
                #print("外部事件进入事件池")
                world_plan = self.calendar[day_index][time_slot]["world_plan"]
                print(world_plan)
                self.agent.external_event_manager.External_event_to_Action(world_plan) #对外部事件进行动作映射

            # ========== 随机活动选择 ========== #
            if self.calendar[day_index][time_slot]['task_planning'] == "":
                life_style_weight = self.calendar[day_index][time_slot]['life_style_weight'] # 日程活动倾向影响
                result = self.agent.select_best_behavior(top_k=2, current_Time_slot=time_slot,life_style_weight = life_style_weight)
                if result[0]:
                    behavior_info = result[0]
                    print(f"🕒 {time_slot.upper()}: {behavior_info['behavior_detail']}")
                    self.calendar[day_index][time_slot]["task_planning"] = behavior_info["behavior_detail"] #这里是不包括执行效果的
                    self.calendar[day_index][time_slot]["task_planning_score"] = behavior_info["score"]
                else:
                    print(f"⚠️ {time_slot.upper()} 当前时段无可选行为")
            else:
                pass
        print("\n")
        #外部事件库根据时间流逝更新
        self.agent.external_event_manager.Updata_External_Event()

    def play_calendar(self,day_index, time_slot):
        """第二遍遍历calendar，生成真实活动"""
        # ==== 天气、假期、外貌等信息 ==== #
        holidayInfo = True
        if random.random()<0.6: 
            holidayInfo = False
        weatherInfo = True
        if random.random()<0.2:
            weatherInfo = False

        print(self.calendar[day_index]['location'] + "," + self.calendar[day_index][time_slot]['weather'] + ",节假日:" + self.calendar[day_index][time_slot]['holiday'])

        task_planning = self.calendar[day_index][time_slot]["task_planning"]
        task_planning_score = self.calendar[day_index][time_slot]["task_planning_score"]

        print(f"🕒 {time_slot.upper()}计划事件: {task_planning}")

        # ==== 判断是否要提供未来事件 ==== #
        task_future_planning = None
        future_day = 0
        future_slot = 0
        future_score = 0
        
        time_slot_index = {"morning": 0, "afternoon": 1, "evening": 2}
        reverse_time_slot = ["morning", "afternoon", "evening"]

        # ==== 判断是否要加入对未来的期待 ==== #
        current_global_index = day_index * 3 + time_slot_index[time_slot]
        if random.random()<0.8:# 按照期待值还是随机选择
            #print("按照期待度最大化选择未来事件")
            future_score_max = 0.0
            future_day_max = 0
            futrue_slot_max = ""
            for iter in range(1,6+2-time_slot_index[time_slot]): # 至少2天，最多2+2个当日阶段
                future_global_index = current_global_index + iter
                if future_global_index < len(self.calendar)*3:
                    future_day = future_global_index // 3
                    future_slot = reverse_time_slot[future_global_index % 3]
                    future_score = float(self.calendar[future_day][future_slot]['task_planning_score'])
                    if future_score > future_score_max:
                        future_day_max = future_day
                        futrue_slot_max = future_slot
                        future_score_max = future_score
            future_day = future_day_max
            future_slot = futrue_slot_max
            future_score = future_score_max
        else:
            #print("执行随机选择未来事件")
            future_global_index = min(len(self.calendar)*3-1,current_global_index + random.randint(1,9+2-time_slot_index[time_slot]))
            future_day = future_global_index // 3
            future_slot = reverse_time_slot[future_global_index % 3]
            future_score = float(self.calendar[future_day][future_slot]['task_planning_score'])

        if future_slot in self.calendar[future_day]:
            if 'task_planning' in self.calendar[future_day][future_slot]:
                if not self.calendar[future_day][future_slot]['task_planning'] == "":   
                    task_future_planning = f"""在{self.calendar[future_day]['date']} {self.calendar[future_day]['weekday']}(Day {future_day})的{future_slot},计划事件是：{self.calendar[future_day][future_slot]['task_planning']},期待值是:{str(future_score)}"""
        
        if future_score > task_planning_score - 0.3:
            delta_score = future_score - task_planning_score
            if random.random() > delta_score + float(time_slot_index[time_slot])*0.3:
                task_future_planning = None #对未来不予期待
            else:
                self.calendar[future_day][future_slot]['task_planning_score'] = future_score + 0.1 #增加对未来具体事情的期待
                print(f"📝 未来事件: {task_future_planning}")
        else:
            task_future_planning = None #对未来不予期待

        if not task_future_planning == None and ("倒霉" in str(task_future_planning) or "失败" in str(task_future_planning)):
            task_future_planning = None #对未来不予期待

        
        # ==== 判断是否要重新对当前事件进行选择 ==== #
        task_actual = None
        re_select = max(0.0,1.0 - self.calendar[day_index][time_slot]["task_planning_score"]) * 2.0
        if random.random() < re_select:
            task_result = "正常"
            # =========== 外部事件处理 =========== #
            if not self.calendar[day_index][time_slot]["world_plan"] == "":
                world_plan = self.calendar[day_index][time_slot]["world_plan"]
                print("外部事件："+world_plan)
                self.agent.external_event_manager.External_event_to_Action(world_plan) # 对外部事件进行动作映射

            # =========== 随机活动选择 =========== #
            if self.calendar[day_index][time_slot]["task_actual"] == "":
                life_style_weight = self.calendar[day_index][time_slot]["life_style_weight"] # 日程活动倾向影响
                result = self.agent.select_best_behavior(top_k=2, current_Time_slot=time_slot,life_style_weight = life_style_weight)
                
                if result[0]:
                    behavior_info = result[0]
                    self.calendar[day_index][time_slot]["task_planning"] = behavior_info["behavior_name"]
                    self.calendar[day_index][time_slot]["task_actual"] = behavior_info["behavior_detail"] + "(" + behavior_info["behavior_result"] + ")"
                    task_actual = self.calendar[day_index][time_slot]["task_actual"]
                    task_result = behavior_info["behavior_result"]
                    if "状况堪忧" in behavior_info["behavior_result"] or "惨遭失败" in behavior_info["behavior_result"]:
                        task_future_planning = None # 如果执行失败，则不再憧憬未来
                    if behavior_info["behavior_detail"] in self.calendar[day_index][time_slot]['task_planning'] or self.calendar[day_index][time_slot]['task_planning'] in behavior_info["behavior_detail"]:
                        task_actual = None # 新计划的和之前计划的一致，则不做处理了
                        task_planning = task_planning + "(结果:" + behavior_info["behavior_result"] + ")"
                    else:
                        print(f"📝 重新做了当前事件的选择: {task_actual}")
                else:
                    print(f"⚠️ {time_slot.upper()} 当前时段无可选行为")
        else:
            # =========== 执行当前规划 =========== #
            task_planning,task_result = self.agent._apply_behavior(self.calendar[day_index][time_slot]['task_planning'],0.5)
            task_planning = task_planning + "(结果:" + task_result + ")"
            if "状况堪忧" in task_result or "惨遭失败" in task_result:
                task_future_planning = None # 如果执行失败，则不再憧憬未来
            

        # ==== 判断是否要回忆 ==== #
        

        # ==== 生成详细内容 ==== #
        task_prompt_file = None
        expression_prompt_file = None

        if random.random()<0.5:# Prompt里有外貌信息
            task_prompt_file = "Fill_Task_Detail_With_Appearance.txt"
            expression_prompt_file = "Expand_Task_Expression_Detail.txt"
        else:# Prompt里无外貌信息
            task_prompt_file = "Fill_Task_Detail_No_Appearance.txt"
            expression_prompt_file = "Expand_Task_Expression_Detail.txt"
                
        if (not task_planning == None and "共情交流" in task_planning) or (not task_actual == None and "共情交流" in task_actual):
            #与用户共情沟通，主动发起一个话题
            task_prompt_file = "Fill_Task_Empathy_With_User.txt"
            expression_prompt_file = "Expand_Empathy_Expression_Detail.txt"
        
        friends = []
        if (not task_planning == None and "社交" in task_planning) or (not task_actual == None and "社交" in task_actual) or (not task_future_planning == None and "社交" in task_future_planning):
            with open("M_file/Friends.json", "r", encoding="utf-8") as f:
                friends = json.load(f)             
        friends = []

        out_t2i = False
        out_expression = False
        out_future = False

        # 当前事件的内容文案生成
        task_detail = self.fill_task_details(
            self.calendar, day_index, time_slot, 
            task_prompt_file, 
            gender = self.agent.gender,
            bio_energy = self.agent.bio_energy,
            task_planning = task_planning, task_planning_score = task_planning_score, 
            task_future = None, task_future_score = 0.0, 
            task_actual = task_actual, 
            holidayInfo = holidayInfo, 
            weatherInfo = weatherInfo, 
            friends = friends
            )
        #if NoExpand == False:
        #    task_detail = self.task_details_expand_user_favorite("Expand_Task_Detail_User_Favorite.txt", task_detail, "动漫")
        print("💬 详细内容：" + task_detail)
        #self.calendar[day_index][time_slot]['task_planning']
        self.calendar[day_index][time_slot]["task_details"] = task_detail

        # 未来期待的内容文案生成
        task_future_detail = ""
        if out_future:
            if (not task_future_planning == None) and (float(future_score)>1.0):
                task_future_detail = self.fill_task_details(
                    self.calendar, day_index, time_slot, 
                    "Prepare_Planning.txt", 
                    task_planning = task_planning, task_planning_score = task_planning_score, 
                    task_future = task_future_planning, task_future_score = future_score, 
                    task_actual = task_actual, 
                    holidayInfo = holidayInfo, 
                    weatherInfo = weatherInfo, 
                    friends = friends
                    )
                print("💬 期待内容：" + task_future_detail)

        # 文生图指令词生成
        task_prompt = ""
        if out_t2i:
            task_prompt = self.task_details_expand(
                    self.calendar, day_index, time_slot, 
                    "Expand_Task_T2I_Prompt_Gen.txt", 
                    task_detail+"事情结果（" + task_result + ")",
                    holidayInfo = holidayInfo, 
                    weatherInfo = weatherInfo, 
                    friends = friends
                    )
            task_prompt = "图片内容:[" + task_prompt + "] 图片格式:[正方形]"
            print("💬 文生图指令：" + task_prompt)

        # 当前的事件心理描述生成
        task_expression = ""
        if out_expression:
            task_expression = self.task_details_expand(
                    self.calendar, day_index, time_slot, 
                    expression_prompt_file, 
                    task_detail+"事情结果（" + task_result + ")",
                    holidayInfo = holidayInfo, 
                    weatherInfo = weatherInfo, 
                    friends = friends
                    )
            print("💬 心理描写：" + task_expression)

        self.agent.print_state()
        print("\n")

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