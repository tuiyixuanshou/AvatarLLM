import LLM_Manager
import json
from dataclasses import dataclass
from typing import List, Dict, Callable, Optional
from tools import load_prompt,save_to_file,ListString
import settings
from datetime import datetime

@dataclass
class EventObject:
    month_index: int
    week_index: int
    Event: str
    Expose: bool

@dataclass
class TargetObject:
    学业成就导向: str
    职业准备导向: str
    个人成长导向: str
    社交关系导向: str

@dataclass
class TargetWeightObject:
    month_index: int
    学业成就权重: float
    职业准备权重: float
    个人成长权重: float
    社交关系权重: float

@dataclass
class WeekPlan:
    weekIndex: int
    week_event: List[Dict]
    @classmethod
    def from_dict(cls, data: Dict):
        # 手动解析 week_event 字段
        week_event = [event for event in data.get('week_event', [])]
        return cls(weekIndex=data['weekIndex'], week_event=week_event)


class Avatar_Events:
    def __init__(self,llm_manager):
        self.llm = llm_manager
        self.events:List[EventObject] = [] #每次生成的客观事件列表
        self.exposed_events:List[EventObject] = [] #每次生成的暴露给计划的事件
    
    #外部事件生成
    def generate_event(self,callback:Optional[Callable] = None):
        print("this is generate")
        prompt = load_prompt("AEvent_Generation")
        
        def generate_event_callback(response:str,error:str):
            print("this is callback")
            if error:
                print(f"事件生成失败:{error}")
                return
            try:
                events_data = json.loads(response)
                self.events = [EventObject(**item) for item in events_data]
                #self.exposed_events = [e for e in self.events if e.Expose]
                self.exposed_events = [e for e in self.events if e.Expose!="false"]
                self.display_events(output_file="Out_Event.txt")
                print(f"事件生成已完毕")
                if callback:callback()
            except Exception as e:
                print(f"callback解析事件数据失败：{str(e)}")
        
        self.llm.user_input_send(prompt,callback=generate_event_callback)

    def display_events(self,output_file: Optional[str] = None):
        """逐个展示 self.events 中的内容"""
        if not self.events:
            print("没有事件可以展示。")
            return
        content = ""
        for index, event in enumerate(self.events, start=1):
            print(f"month_index: {event.month_index}")
            print(f"week_index: {event.week_index}")
            print(f"Event: {event.Event}")
            print(f"Expose: {event.Expose}")
            print("-" * 30) 
            content += f"month_index: {event.month_index}\n"
            content += f"week_index: {event.week_index}\n"
            content += f"Event: {event.Event}\n"
            content += f"Expose: {event.Expose}\n"
            content += "-" * 30 + "\n"
        
        if output_file:
            now = datetime.now()
            formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
            timeRecord = f"\n外部安排事件创建时间:{formatted_time}\n"
            save_to_file(output_file,timeRecord,"a")
            save_to_file(output_file,content,"a")


class Avatar_Self:
    def __init__(self,llm_manager):
        self.llm = llm_manager
        self.target:List[TargetObject] = []
        self.weights: List[TargetWeightObject] = []
        self.weekplans:List[WeekPlan] = []
    #Avatar自身总目标生成
    def generate_targets(self,callback: Optional[Callable] = None):
        prompt = load_prompt("APlan_Target")

        def generate_targets_callback(response:str,error:str):
            print("Event数据解析:\n")
            if error:
                print(f"事件生成失败:{error}")
                return
            try:
                target_data = json.loads(response)
                self.target = [TargetObject(**item) for item in target_data]
                if callback:callback()
                print(f"事件生成已完毕")
                self.display_targets(output_file="Avatar_Target.txt")
            except Exception as e:
                print(f"callback解析事件数据失败：{str(e)}")
        
        self.llm.user_input_send(prompt,callback=generate_targets_callback)
    
    def display_targets(self,output_file: Optional[str] = None):
        """逐个展示 self.targets 中的内容"""
        if not self.target:
            print("没有事件可以展示。")
            return
        
        content = ""
        for index, target in enumerate(self.target, start=1):
            print(f"个人成长导向: {target.个人成长导向}")
            print(f"学业成就导向: {target.学业成就导向}")
            print(f"社交关系导向: {target.社交关系导向}")
            print(f"职业准备导向: {target.职业准备导向}")
            print("-" * 30) 
            content += f"个人成长导向: {target.个人成长导向}\n"
            content += f"学业成就导向: {target.学业成就导向}\n"
            content += f"社交关系导向: {target.社交关系导向}\n"
            content += f"职业准备导向: {target.职业准备导向}\n"
            content += "-" * 30 + "\n"
        
        if output_file:
            now = datetime.now()
            formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
            timeRecord = f"\n个人驱动目标 创建时间:{formatted_time}\n"
            save_to_file(output_file,timeRecord,"a")
            save_to_file(output_file,content,"a")
    

    def APlan_TargetWeigh(self,exposed_events:List[EventObject], callback: Optional[Callable] = None):
        prompt = load_prompt("APlan_TargetWeigh") + ListString.list_to_string(exposed_events)
        print(prompt)
        def APlan_TargetWeigh_callback(response:str,error:str):
            if error:
                print(f"目标权重生成失败:{error}")
                return
            try:
                targetweigh_data = json.loads(response)
                self.weights = [TargetWeightObject(**item) for item in targetweigh_data]
                if callback:callback()
                print(f"事件生成已完毕")
                self.display_targetsweigh(output_file="Avatar_Target.txt")
            except Exception as e:
                print(f"callback解析事件数据失败：{str(e)}")
        
        self.llm.user_input_send(prompt,callback=APlan_TargetWeigh_callback)

    def display_targetsweigh(self,output_file: Optional[str] = None):
        """逐个展示 self.targetstargetsweigh 中的内容"""
        if not self.weights:
            print("没有事件可以展示。")
            return
        
        content = ""
        for index, weight in enumerate(self.weights, start=1):
            print(f"month_index: {weight.month_index}")
            print(f"个人成长权重: {weight.个人成长权重}")
            print(f"学业成就权重: {weight.学业成就权重}")
            print(f"社交关系权重: {weight.社交关系权重}")
            print(f"职业准备权重: {weight.职业准备权重}")
            print("-" * 30) 
            content += f"month_index: {weight.month_index}\n"
            content += f"个人成长权重: {weight.个人成长权重}\n"
            content += f"学业成就权重: {weight.学业成就权重}\n"
            content += f"社交关系权重: {weight.社交关系权重}\n"
            content += f"职业准备权重: {weight.职业准备权重}\n"
            content += "-" * 30 + "\n"

        if output_file:
            now = datetime.now()
            formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
            timeRecord = f"\n每月侧重目标导向 创建时间:{formatted_time}\n"
            save_to_file(output_file,timeRecord,"a")
            save_to_file(output_file,content,"a")

    
    def APlan_SpecifyPlan(self,targets:List[TargetObject],targetweighs:List[TargetWeightObject],callback: Optional[Callable] = None):
        cur_targetweigh = [targetweighs[settings.MONTH_INDEX-1]]
        prompt1 = f"""现在你扮演的大学生进入了第1个月。回忆一下，总核心目标为:{ListString.list_to_string(targets)},
本月的核心目标的权重分配为:{ListString.list_to_string(cur_targetweigh)}.
你需要在事件池中，每周选择本周的事件安排.事件池：{load_prompt("Event_Pool")}."""
        prompt2 = load_prompt("APlan_SpecifyPlan")
        prompt = prompt1+prompt2
        print(prompt)

        def APlan_SpecifyPlan_callback(response:str,error:str):
            if error:
                print(f"目标权重生成失败:{error}")
                return
            try:
                plan_data = json.loads(response)
                self.weekplans = [WeekPlan.from_dict(item) for item in plan_data]
                if callback:callback()
                print(f"事件生成已完毕")
                self.display_weekplan(output_file="Avatar_Target.txt")
            except Exception as e:
                print(f"callback解析事件数据失败：{str(e)}")

        self.llm.user_input_send(prompt,callback=APlan_SpecifyPlan_callback)

    def display_weekplan(self,output_file: Optional[str] = None):
        """逐个展示 self.weekplans 中的内容"""
        if not self.weekplans:
            print("没有计划可以展示。")
            return
        
        content = ""
        for index, plan in enumerate(self.weekplans, start=1):
            print(f"周 {index}:")
            print(f"  周索引: {plan.weekIndex}")
            content += f"周 {index}:\n"
            content += f"  周索引: {plan.weekIndex}\n"
            for event in plan.week_event:
                print(f"    类型: {event['type']}")
                print(f"    驱动类型: {event['driven_type']}")
                print(f"    具体事件: {event['specify_event']}")
                print("-" * 30)
                content += f"    类型: {event['type']}\n"
                content += f"    驱动类型: {event['driven_type']}\n"
                content += f"    具体事件: {event['specify_event']}\n"
                content += "-" * 30 + "\n"
        content+="Avatar行为树生成完毕！输入“test”进行前四周故事生成和单帧图片\n"
        if output_file:
            now = datetime.now()
            formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
            timeRecord = f"\n每月计划事件 创建时间:{formatted_time}\n"
            save_to_file(output_file,timeRecord,"a")
            save_to_file(output_file,content,"a")
        