from openai import OpenAI
import json
from typing import Dict, Any, List, Optional
import numpy as np
import re
import os

from datetime import datetime
#import datetime

class ExternalEventPlanner:
    def __init__(self):
        self.social_phases_macro = ""
    
        log_path = "M_file/social_phases_macro.json"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                try:
                    self.social_phases_macro = json.load(f)
                except Exception:
                    print("❌社会属性内容不存在！")
        else:
            print("❌社会属性内容不存在！")

    def rule_condition(self,day_date: str, weekday: str, prerequisite_condition: dict):
        date_obj = datetime.strptime(day_date, "%Y-%m-%d")

        #日期匹配
        date_ranges = prerequisite_condition.get("date_range", [])
        if date_ranges:
            in_any_range = False
            for start, end in date_ranges:
                start_date = datetime.strptime(start, "%Y-%m-%d")
                end_date = datetime.strptime(end, "%Y-%m-%d")
                if start_date <= date_obj <= end_date:
                    in_any_range = True
                    break
            if not in_any_range:
                return False  # 日期不符合

        #星期匹配
        weekdays = prerequisite_condition.get("weekday_in", [])
        if weekdays:
            if weekday not in weekdays:
                return False  # 星期不符合

        #没限制
        return True
    
    def get_matching_social_phases_macro(self,day_date: str, weekday: str):
        matched_ranges = []
        for phases in self.social_phases_macro:
            if self.rule_condition(day_date,weekday,phases["prerequisite_condition"]):
                influence_range = phases.get("behavior_influence_range", None)
                if influence_range:
                    matched_ranges.append(influence_range)
        return matched_ranges




class ExternalEventManager:
    def __init__(self, ExternalEvent_path: str):
        self.event_path = ExternalEvent_path
        self.External_event_pool: Dict[str, Dict[str, Any]] = {}
        #初始化
        self.save_External_event_init()
        self.save_External_event_log_init()
        self.External_Planner = ExternalEventPlanner()


    """读取外部事件库"""
    def load_External_event(self) -> Dict[str, Dict[str, Any]]:
        try:
            with open(self.event_path, 'r', encoding='utf-8') as f:
                db = json.load(f)
                # Weight字段自动转np.array
                for event, info in db.items():
                    if 'Weight' in info and isinstance(info['Weight'], list):
                        info['Weight'] = np.array(info['Weight'])
                return db
        except FileNotFoundError:
            return {}
    
    """将外部事件存储到本地"""
    def save_External_event(self):
        db_copy = {}
        for event, info in self.External_event_pool.items():
            info_copy = info.copy()
            # Weight字段转回list以支持json序列化
            if 'Weight' in info_copy and isinstance(info_copy['Weight'], np.ndarray):
                info_copy['Weight'] = info_copy['Weight'].tolist()
            db_copy[event] = info_copy

        # 1. 先序列化为字符串
        json_str = json.dumps(db_copy, ensure_ascii=False, indent=2)
        # 2. 正则合并多行数组为一行
        json_str = re.sub(r'\[\s*((?:[^\[\]]|\n)+?)\s*\]',lambda m: '[' + ' '.join(m.group(1).replace('\n', '').split()) + ']',
            json_str
            )
        
        with open(self.event_path, 'w', encoding='utf-8') as f:
            #json.dump(db_copy, f, ensure_ascii=False, indent=2)
            f.write(json_str)


    """外部事件记录-仅查看用"""
    def save_External_event_log(self, new_events: Dict[str, Dict[str, Any]]):
        # 按事件条目写入，每个条目一行，便于后期分析
        log_path = "M_file/External_Event_log.json"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                try:
                    logs = json.load(f)
                except Exception:
                    logs = []
        else:
            logs = []

        now = datetime.datetime.now().isoformat()
        for event, info in new_events.items():
            info_copy = info.copy()
            if 'Weight' in info_copy and isinstance(info_copy['Weight'], np.ndarray):
                info_copy['Weight'] = info_copy['Weight'].tolist()
            logs.append({
                "timestamp": now,
                "event": event,
                "info": info_copy
            })

        json_str = json.dumps(logs, ensure_ascii=False, indent=2)
        # 2. 正则合并多行数组为一行
        json_str = re.sub(r'\[\s*((?:[^\[\]]|\n)+?)\s*\]',lambda m: '[' + ' '.join(m.group(1).replace('\n', '').split()) + ']',
            json_str
        )
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(json_str)

    def save_External_event_init(self):
        self.External_event_pool= {}
        self.save_External_event()

    def save_External_event_log_init(self):
        log_path = "M_file/External_Event_log.json"
        with open(log_path, 'w') as file:
            json.dump([], file)

    def save_External_event(self):
        db_copy = {}
        for event, info in self.External_event_pool.items():
            info_copy = info.copy()
            # Weight字段转回list以支持json序列化
            if 'Weight' in info_copy and isinstance(info_copy['Weight'], np.ndarray):
                info_copy['Weight'] = info_copy['Weight'].tolist()
            db_copy[event] = info_copy

        # 1. 先序列化为字符串
        json_str = json.dumps(db_copy, ensure_ascii=False, indent=2)
        # 2. 正则合并多行数组为一行
        json_str = re.sub(r'\[\s*((?:[^\[\]]|\n)+?)\s*\]',lambda m: '[' + ' '.join(m.group(1).replace('\n', '').split()) + ']',
            json_str
            )
        
        with open(self.event_path, 'w', encoding='utf-8') as f:
            #json.dump(db_copy, f, ensure_ascii=False, indent=2)
            f.write(json_str)
    
    def process_output(self, output: str) -> bool:
        """处理LLM生成的外部事件json字符串，解析并存入self.External_event_pool"""
        self.External_event_pool = {}
        self.External_event_pool = self.load_External_event()
        if output is None:
            return False
        try:
            output = output.replace("```", "").replace("json", "").strip()
            event_dict = json.loads(output)
            self.save_External_event_log(event_dict)
            # 合并进事件池
            for name, content in event_dict.items():
                # Weight 字段转为 np.array 方便后续采样
                if 'Weight' in content and isinstance(content['Weight'], list):
                    content['Weight'] = np.array(content['Weight'])
                self.External_event_pool[name] = content
            self.save_External_event()
            #print("外部事件添加成功！")
            return True
        except json.JSONDecodeError as e:
            print(f"[WARN] 外部事件json解析错误: {e}")
            return False
    
    def External_event_to_Action(self,event_desc:str):
        """外部事件映射为动作并被写入外部事件池中"""

        """这用External_event_toAction.txt中的prompt直接生成外部事件--->动作的映射"""

        client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")
        message = [{"role": "system", "content": self.load_prompt("External_event_toAction.txt")}]
        message.append({"role": "user", "content": f"外部事件：{event_desc}"})

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=message,
            stream=False
        )

        #print(response.choices[0].message.content)
        self.process_output(response.choices[0].message.content)

    
    def load_prompt(self,filename: str) -> str:
        file_path = f'prompt_zh/{filename}'
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except:
            print(f"{filename}读取失败")
            system_prompt = ""
        return system_prompt
    
    def Updata_External_Event(self):
        self.External_event_pool = {}
        self.External_event_pool = self.load_External_event()

        if len(self.External_event_pool) == 0:
            return
        
        to_del = []
        for event, info in list(self.External_event_pool.items()):
            if 'choice_bias' in info and 'choice_decay' in info:
                info['choice_bias'] = info['choice_bias'] - info['choice_decay']
                if info['choice_bias'] <= 0:
                    to_del.append(event)
    
        for event in to_del:
            del self.External_event_pool[event]
        # 明确保存的是 self.External_event_to_Action
        self.save_External_event()
        print("外部事件库更新内容")

        


#externalManager = ExternalEventManager("M_file/External_Event.json")
#externalManager.External_event_to_Action("地震了")
