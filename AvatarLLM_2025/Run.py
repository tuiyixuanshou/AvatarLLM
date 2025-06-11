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

import Avatar

if __name__ == "__main__":
    user_info = "女性,23岁,喜欢动漫,萌宠,不喜欢聊天"

    with open("M_file/Event_pool.json", "r", encoding="utf-8") as f:
        behavior_library = json.load(f)
    agent = Avatar.VirtualAgent(Avatar.personality2, Avatar.emotional1, behavior_library)
    agent.print_state()
    agent.gen_calender() #生成日历
    agent.calendar_module.save_calendar()

    #agent.dialogue_module.dialog_mode_ai_emotionally_supportive(user_info=user_info,type="问候",system_file="Dialogue_Persona.txt")
    agent.dialogue_module.dialog_mode_ai_self_disclosure(user_info = user_info, type = "", system_file = "Dialogue_Persona.txt")

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            print("Exiting the Dialogue Module. Goodbye!")
            break
        
        agent.dialogue_module.dialog_mode_communication_ai_with_user(user_input,user_info=user_info,system_file="Dialogue_Persona_Single.txt")