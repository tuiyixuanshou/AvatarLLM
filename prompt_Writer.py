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

    def generate_Singlevideo_prompt(self, avatar_respond, callback):
        #prompt = load_prompt("Video_Promptnew") +f"agent模拟活动内容描述：{avatar_respond}"
        prompt = f"""
主体:已原图中已有的白色小动物为主体
主体动作:角色坐在服务器机房中，聚精会神地敲击键盘，屏幕上显示出用 Processing 制作的粒子动画；几秒后，角色瞪大眼睛，轻轻扬眉，露出“成了！”的惊喜神情。
符合运动规律
场景:保持原图中已有的场景不变
镜头语言:保持镜头固定不变
光影:机房整体为低光蓝调，服务器上的指示灯点点闪烁；屏幕投射出的绿色代码光映在角色脸上，粒子动画启动时，屏幕亮度骤增，投射出柔和但科幻感十足的光晕，瞬间照亮角色表情。
氛围:略带神秘、沉浸式科技氛围，带有“深夜偷偷搞点炫技小创作”的少年感；节奏感由静转动，从代码敲击到动画绽放形成小高潮，像是“苦读之余悄悄点燃的灵感之火”。
"""
        print(prompt)
        callback(prompt)

        def on_video_prompt_ready(response: str, error: str):
            print("Kling 视频 Prompt:", response)
            callback(response)

        #settings.Prompt_manager.user_input_send(prompt, callback=on_video_prompt_ready, type="string")