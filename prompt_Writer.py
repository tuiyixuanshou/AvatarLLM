import settings
from tools import load_prompt,save_to_file,ListString
from typing import List, Dict, Callable, Optional
from datetime import datetime

def write_Prompt(output_file,content):
    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
    timeRecord = f"\nImage_Prompt 创建时间:{formatted_time}\n"
    save_to_file(output_file,timeRecord,"a")
    save_to_file(output_file,content+"\n","a")
    save_to_file(output_file,"-"*30+"\n","a")

def Image_Prompt_Writer(avater_respond):
    prompt = load_prompt("Image_PromptWriter")+avater_respond+"这是大学生生活中可能的活动地点场景池，请你选择一个场景进行描述："+load_prompt("Scene_Pool")
    print("Image_Prompt_Writer:",prompt,"\n")
    def Image_Prompt_Writer_callback(response:str,error:str):
        print("This is Kling_Prompt:",response)
        write_Prompt("Image_Prompt.txt",response)
        #KlingAPI.Kling_API_Image(response) #写好prompt之后直接利用可灵生成

    settings.Prompt_manager.user_input_send(prompt,callback=Image_Prompt_Writer_callback,type="string")

class AvatarImageVideoGenerator:
    def __init__(self, output_prompt_file="Image_Prompt.txt"):
        self.output_prompt_file = output_prompt_file
        self.prompt_result = ""

    def write_prompt_to_file(self, content):
        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        save_to_file(self.output_prompt_file, f"\nImage_Prompt 创建时间:{formatted_time}\n", "a")
        save_to_file(self.output_prompt_file, content + "\n", "a")
        save_to_file(self.output_prompt_file, "-" * 30 + "\n", "a")

    def generate_image_prompt(self, avatar_respond: str, callback):
        prompt = load_prompt("Image_PromptWriter") + avatar_respond + \
                 "这是大学生生活中可能的活动地点场景池，请你选择一个场景进行描述：" + load_prompt("Scene_Pool")

        def on_prompt_ready(response: str, error: str):
            print("Kling 图像 Prompt:", response)
            self.prompt_result = response
            self.write_prompt_to_file(response)
            callback(response)

        settings.Prompt_manager.user_input_send(prompt, callback=on_prompt_ready, type="string")

    def generate_video_prompt(self, image_url: str,avatar_respond, callback):
        prompt = load_prompt("Video_PromptWriter") + f" 图片地址: {image_url}"+f"agent模拟活动内容：{avatar_respond}"

        def on_video_prompt_ready(response: str, error: str):
            print("Kling 视频 Prompt:", response)
            callback(response)

        settings.Prompt_manager.user_input_send(prompt, callback=on_video_prompt_ready, type="string")