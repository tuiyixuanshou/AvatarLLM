import settings
from tools import load_prompt,ListString
from typing import List, Dict, Callable, Optional
import KlingAPI



def Image_Prompt_Writer(avater_respond):
    prompt = load_prompt("Image_PromptWriter")+avater_respond
    print("Image_Prompt_Writer:",prompt,"\n")
    def Image_Prompt_Writer_callback(response:str,error:str):
        print("This is Kling_Prompt:",response)
        KlingAPI.Kling_API_Image(response) #写好prompt之后直接利用可灵生成

    settings.Prompt_manager.user_input_send(prompt,callback=Image_Prompt_Writer_callback,type="string")