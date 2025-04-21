import LLM_Manager
import Avatar_Driven_module
API_KEY = "sk-cjktrxbohzgcvvcgkeppefasertnysxdmerrowgadqkciews"
BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"

"""Kling密钥"""
AK = "f5c4e53b02ed4d6d905d8875cc841240" # 填写access key
SK = "3f2c670a6592497e9f4982021d115ae7" # 填写secret key
KLING_URL = "https://api.klingai.com"
KLING_IMAGE_URL= "https://api.klingai.com/v1/images/generations"

MONTH_INDEX = 1
WEEK_INDEX = 1

MODEL_NAME = "meta-llama/Llama-3.3-70B-Instruct"
SYSTEM_PROMPT = "你是一个治愈小精灵"

"""Plan_manager Event_manager passive_dial_manager分别对应三个Agent，拥有独立上下文"""
passive_dial_manager = LLM_Manager.LLM_Manager(BASE_URL,API_KEY,MODEL_NAME,SYSTEM_PROMPT)
Plan_manager = LLM_Manager.LLM_Manager(BASE_URL,API_KEY,MODEL_NAME)
Event_manager = LLM_Manager.LLM_Manager(BASE_URL,API_KEY,MODEL_NAME)

PROMPT_SYSTEM = "你是一个经验丰富的AIGCprompt的撰写者,你也有丰富的心理学经验。"
Prompt_manager = LLM_Manager.LLM_Manager(BASE_URL,API_KEY,MODEL_NAME,PROMPT_SYSTEM)

M_Avatar_Target = Avatar_Driven_module.Avatar_Self(Plan_manager)
M_Avatar_Event = Avatar_Driven_module.Avatar_Events(Event_manager)