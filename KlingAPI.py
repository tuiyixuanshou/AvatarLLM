import LLM_Manager
import json
import requests
import time
import jwt
import settings
from threading import Thread

ak = settings.AK
sk = settings.SK

"""可灵图片生成公开办法"""
def Kling_API_Image(image_prompt):
    print("KlingAPI:Start Kling Generation")
    Thread(target=_async_Kling_Image_Generation, args=(image_prompt,handle_image_url)).start()

def _async_Kling_Image_Generation(image_prompt,callback=None):
    try:
        response = _Kling_Image_Generation(image_prompt)
        print("Kling_Image responde:\n"+ response)
        if response["code"] == 200:
            task_ID = response["data"]["task_id"]
            error = None
        else:
            task_ID = "0"
            print("Kling_Task_Generation_False")
    except Exception as e:
        response = None
        task_ID = "0"
        error = str(e)
        print(error)
    finally:
        print("task ID:",task_ID)
            
    if callback:
        if task_ID != "0":
            print("Start kling Auto Check:")
            _auto_check_task_status(task_ID,callback)

    

def _Kling_Image_Generation(image_prompt):
    api_token = encode_jwt_token(ak,sk)
    headers = {
    "Authorization": f"Bearer {api_token}",  # 替换为你的实际 Token
    "Content-Type": "application/json"
    }

    data = {
    "model_name":"kling-v1-5",              
    "prompt":image_prompt,
    "negative_prompt" :"模糊不清，抽象，恐怖谷，恐怖",
    "n":1,
    "aspect_ratio":"9:16"
    }
    response = requests.post(settings.KLING_IMAGE_URL, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.json()

def _auto_check_task_status(task_id, callback=None):
    api_token = encode_jwt_token(ak,sk)
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    url = settings.KLING_IMAGE_URL+f"/{task_id}"

    cur_task_status = "processing"
    cur_respond = ""

    while cur_task_status != "succeed":
        time.sleep(10) 
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Request Error: {response.status_code} - {response.text}")
            break
        cur_respond = response.json()
        cur_task_status = cur_respond.get("data", {}).get("task_status", "processing")
        print(f"Task Status: {cur_task_status}")

    if cur_task_status == "succeed" and cur_respond:
        image_url = cur_respond.get("data", {}).get("task_result", {}).get("images", [{}])[0].get("url", "")
        print(f"Generated Image URL: {image_url}")
        callback(image_url)
    else:
        print("图片查询时遇到问题！")
        callback(None)

def handle_image_url(image_url):
    if image_url:
        print(f"Generated Image URL: {image_url}")
    else:
        print("图片查询时遇到问题！")

def encode_jwt_token(ak, sk):
    headers = {
        "alg": "HS256",
        "typ": "JWT"
    }
    payload = {
        "iss": ak,
        "exp": int(time.time()) + 1800, # 有效时间，此处示例代表当前时间+1800s(30min)
        "nbf": int(time.time()) - 5 # 开始生效的时间，此处示例代表当前时间-5秒
    }
    
    token = jwt.encode(payload, sk, headers=headers)
    return token

