import LLM_Manager
import Avatar_Driven_module
from tools import load_prompt
API_KEY = "sk-cjktrxbohzgcvvcgkeppefasertnysxdmerrowgadqkciews"
BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"

"""Kling密钥"""
AK = "c3970369462b4047bc666355b598e449" # 填写access key
SK = "1c85901908b9472b924c0d4ffc7e75db" # 填写secret key
KLING_URL = "https://api.klingai.com"
KLING_IMAGE_URL= "https://api.klingai.com/v1/images/generations"

"""端脑云网址"""
Cephalon_Creat_Task = "https://wp05.unicorn.org.cn:17206/api/prompt"
Cephalon_Check_Task = "https://wp05.unicorn.org.cn:17206/history/"


MONTH_INDEX = 1
WEEK_INDEX = 1

MODEL_NAME = "meta-llama/Llama-3.3-70B-Instruct"
SYSTEM_PROMPT = load_prompt("System_Prompt.json")

"""Plan_manager Event_manager passive_dial_manager分别对应三个Agent，拥有独立上下文"""
passive_dial_manager = LLM_Manager.LLM_Manager(BASE_URL,API_KEY,MODEL_NAME,SYSTEM_PROMPT)
Plan_manager = LLM_Manager.LLM_Manager(BASE_URL,API_KEY,MODEL_NAME,SYSTEM_PROMPT)
Event_manager = LLM_Manager.LLM_Manager(BASE_URL,API_KEY,MODEL_NAME,SYSTEM_PROMPT)

PROMPT_SYSTEM = "你是一个经验丰富的AIGCprompt的撰写者,你也有丰富的心理学经验。"
Prompt_manager = LLM_Manager.LLM_Manager(BASE_URL,API_KEY,MODEL_NAME,PROMPT_SYSTEM)

M_Avatar_Target = Avatar_Driven_module.Avatar_Self(Plan_manager)
M_Avatar_Event = Avatar_Driven_module.Avatar_Events(Event_manager)