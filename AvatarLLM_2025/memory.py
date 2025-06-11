import os
import json
from datetime import datetime

class Memory:
    def __init__(self,max_short_memory = 20, max_recent_events = 5):
        self.dialogue_persona = ""
        self.dialogue_stratagy = ""
        self.max_short_memory = max_short_memory
        self.short_term_memory = self.load_memory_local("all_memory.jsonl",self.max_short_memory)
        self.max_recent_events = max_recent_events
        self.recent_proactive_event = self.load_memory_local("proactive_event.jsonl",self.max_recent_events)

    #加载本地短期记忆    
    def load_memory_local(self,path,max):
        memory_path = f"memory/{path}"
        if not os.path.exists(memory_path):
            with open(memory_path, 'w', encoding='utf-8') as file:
                pass  # 创建一个空文件
        try:
            memory = []
            with open(memory_path, 'r', encoding='utf-8') as file:
                for line in file:
                    if line.strip(): 
                        try:
                            memory.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            print(f"Warning: Skipping invalid JSON line: {line.strip()}")
        
            #返回规定数量的记录
            return memory[-max:]

        except FileNotFoundError:
            return []
    
    def store_short_term_memory(self, entries):
        memory_path = "memory/all_memory.jsonl"
        if not os.path.exists(memory_path):
            open(memory_path, 'w', encoding='utf-8').close()

        with open(memory_path, 'a', encoding='utf-8') as file:
            for i in entries:
                self.short_term_memory.append(i) #先加入到short_term_memory
                try:
                    json_record = json.dumps(i, ensure_ascii=False) #持久化到本地
                    file.write(json_record + '\n')
                except (TypeError, ValueError) as e:
                    print(f"❌Error: Unable to write record to file. Invalid JSON format: {i}. Error: {e}")
        
        #直接删去多余的短期记忆 是否要加入embedding？
        if len(self.short_term_memory) > self.max_short_memory:
            # Transfer the 2nd and 3rd entries to long-term memory (1st is system_prompt)
            if self.short_term_memory[0]["role"]=="assistant":
                del self.short_term_memory[0]
            del self.short_term_memory[0:2]
    
    def store_Proactive_Event(self,date,time_slot,proactive_message):
        memory_path = "memory/proactive_event.jsonl"
        if not os.path.exists(memory_path):
            open(memory_path, 'w', encoding='utf-8').close()
        
        #trigger_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        Event_history_log = {"date":date,"time_slot":time_slot,"message":proactive_message}
        with open(memory_path, 'a', encoding='utf-8') as file:
            try:
                json_record = json.dumps(Event_history_log, ensure_ascii=False) #持久化到本地
                file.write(json_record + '\n')
            except (TypeError, ValueError) as e:
                print(f"❌Error: Unable to write record to proactive_event. Invalid JSON format: {Event_history_log}. Error: {e}")
        
        if len(self.recent_proactive_event) > self.max_recent_events:
            del self.short_term_memory[0]

