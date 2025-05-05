import json
import requests
import time
import jwt
import settings
from threading import Thread
from tools import load_prompt,save_to_file
import Image_Generation

ak = settings.AK
sk = settings.SK
ak_video = settings.AK_VIDEO
sk_video = settings.SK_VIDEO

"""可灵图片生成公开办法"""
def Kling_API_Image(image_prompt,callback = None):
    print("KlingAPI:Start Kling Generation")
    Thread(target=_async_Kling_Image_Generation, args=(image_prompt,callback)).start()

def _async_Kling_Image_Generation(image_prompt,callback=None):
    try:
        response = _Kling_Image_Generation(image_prompt)
        print("Kling_Image responde:\n", {response["code"]})
        print(response)
        if response["code"] == 0:
            task_ID = response["data"]["task_id"]
            error = None
        else:
            task_ID = "0"
            print("Kling_Task_Generation_False")
    except Exception as e:
        response = None
        task_ID = "0"
        error = str(e)
        print("error:",error)
    finally:
        print("task ID:",task_ID)
            
    if callback:
        if task_ID != "0":
            print("Start kling Auto Check:")
            _auto_check_task_status(task_ID,callback)

    

def _Kling_Image_Generation(image_prompt):
    api_token = encode_jwt_token(ak,sk)
    print(api_token)
    headers = {
    "Authorization": f"Bearer {api_token}",  # 替换为你的实际 Token
    "Content-Type": "application/json"
    }
    ImageBase64 = load_prompt("avatar.txt")
    data = {
    "model_name":"kling-v1-5",              
    "prompt":image_prompt,
    "negative_prompt" :"模糊不清，抽象，恐怖谷，恐怖",
    "image":ImageBase64,
    "image_reference":"subject",
    "image_fidelity":0.9,
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
        callback(image_url,)
    else:
        print("图片查询时遇到问题！")
        callback(None)

# def handle_image_url(image_url):
#     if image_url:
#         print(f"Generated Image URL: {image_url}")
#         save_to_file("Avatar_Story.txt",image_url,"a")
#         print("开始生成视频：")
#     else:
#         print("图片查询时遇到问题！")

def Kling_API_Video(prompt, image_url):
    Thread(target=_async_Kling_Video_Generation, args=(prompt, image_url,handle_video_url)).start()

def _async_Kling_Video_Generation(video_prompt,image_url,callback=None):
    try:
        response = _Kling_Video_Generation(video_prompt,image_url)
        if response == None:
            print("视频任务创建失败！")
            return
        print("Kling_Video responde:\n", {response["code"]})
        print(response)
        if response["code"] == 0:
            task_ID = response["data"]["task_id"]
            error = None
        else:
            task_ID = "0"
            print("Kling_Task_Generation_False")
    except Exception as e:
        response = None
        task_ID = "0"
        error = str(e)
        print("error:",error)
    finally:
        print("task ID:",task_ID)
            
    if callback:
        if task_ID != "0":
            print("Start kling Auto Check:")
            _auto_check_video_status(task_ID,callback)

def _Kling_Video_Generation(prompt, image_url):
    try:
        api_token = encode_jwt_token(ak_video,sk_video)
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        data = {
            "model_name": "kling-v1-6",
            "image": image_url,
            "image_tail": image_url,
            "prompt": prompt,
            "cfg_scale": 0.85,
            "mode": "pro"
        }
        response = requests.post(settings.KLING_VIDEO_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("视频生成异常:", e)
        return None

def _auto_check_video_status(task_id, callback):
    url = (settings.KLING_VIDEO_URL+ f"/{task_id}")
    token = encode_jwt_token(ak_video,sk_video)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
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
        video_url = cur_respond.get("data", {}).get("task_result", {}).get("videos", [{}])[0].get("url", "")
        print(f"Generated Video URL: {video_url}")
        callback(video_url)
    else:
        print("视频查询时遇到问题！")
        callback(None)

def handle_video_url(video_url):
    if video_url:
        print(f"Generated Image URL: {video_url}")
        save_to_file("Avatar_Story.txt",video_url+"\n","a")
        if settings.WEEK_INDEX<=3:
            settings.WEEK_INDEX = settings.WEEK_INDEX+1
            #Avatar_Driven_Respond.Avatar_Proactive(prompt_Writer.Image_Prompt_Writer)
            Image_Generation.Avatar_Proactive_Image()
        else:
            print("结束生成")

    else:
        print("视频查询时遇到问题！")

def encode_jwt_token(ak, sk):
    payload = {
        "iss": ak,
        "exp": int(time.time()) + 1800,
        "nbf": int(time.time()) - 30
    }
    headers = {
        "typ": "JWT",
        "alg": "HS256"
    }
    token = jwt.encode(payload=payload, key=sk, algorithm="HS256", headers=headers)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

# if __name__ == "__main__":
#     Kling_API_Image("""scene": "University Study Lounge with Whiteboard at Dusk","elements": {
#     "protagonist_pose": "leaning over desk with flowcharts spread out",
#     "background_details": [
#       "sunset light through bay windows",
#       "whiteboard covered with binary tree diagrams",
#       "algorithm textbook open to chapter 7",
#       "multiple colored pens arranged beside notebooks",
#       "laptop showing LeetCode competition countdown timer",")"half-finished bubble tea with condensation drops",
#     "protagonist_pose": "leaning over desk with flowcharts spread out""")
    

