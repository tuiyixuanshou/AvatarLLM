import settings
from tools import load_prompt,save_to_file,ListString
from typing import List, Dict, Callable, Optional
import KlingAPI
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
        KlingAPI.Kling_API_Image(response) #写好prompt之后直接利用可灵生成

    settings.Prompt_manager.user_input_send(prompt,callback=Image_Prompt_Writer_callback,type="string")