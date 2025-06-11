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
    with open("M_file/Event_pool.json", "r", encoding="utf-8") as f:
        behavior_library = json.load(f)
    agent = Avatar.VirtualAgent(Avatar.personality2, Avatar.emotional1, behavior_library)
    agent.print_state()
    agent.gen_calender() #生成日历

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            print("Exiting the Dialogue Module. Goodbye!")
            break
        
        agent.dialogue_module.llm_reply(user_input,"Dialogue_Persona.txt")