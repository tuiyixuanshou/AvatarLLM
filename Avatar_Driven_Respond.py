import json
import settings
from tools import load_prompt,save_to_file,ListString
from dataclasses import dataclass
from typing import List, Dict, Callable, Optional
from datetime import datetime
import prompt_Writer

@dataclass
class AvatarResObject:
    respond_type: str
    respond: str
    user_choice: List[Dict]
    @classmethod
    def from_dict(cls, data: Dict):
        # 手动解析字段
        user_choice = data.get('user_choice', [])
        return cls(respond_type=data.get('respond_type', ''),respond=data.get('respond', ''),user_choice=user_choice)

def Avatar_Proactive(callback:Optional[Callable] = None):
    cur_targetweigh = [settings.M_Avatar_Target.weights[settings.MONTH_INDEX-1]]
    prompt1 = load_prompt("ARes")
    prompt2 = f"""
在这段时间中，核心目标选择：{ListString.list_to_string(settings.M_Avatar_Target.target)}
本月四种核心目标的权重分布：{ListString.list_to_string(cur_targetweigh)}
现在进入了第{settings.MONTH_INDEX}个月的第{settings.WEEK_INDEX}个星期，
周计划：{ListString.list_to_string(settings.M_Avatar_Target.weekplans[(settings.MONTH_INDEX-1)*4+settings.WEEK_INDEX-1].week_event)}
事件：{settings.M_Avatar_Event.events[(settings.MONTH_INDEX - 1) * 4 + settings.MONTH_INDEX - 1].Event}"""
    prompt = prompt1+prompt2
    
    def Avatar_Proactive_callback(response:str,error:str):
        print("Avatar_Proactive_callback")
        if error:
            print(f"事件生成失败:{error}")
            return
        try:
            response_data = json.loads(response)
            Avatar_response = [AvatarResObject.from_dict(item) for item in response_data]
            avatar_string = display_Avatar_response(Avatar_response,output_file="Avatar_Story.txt")
            print(f"事件生成已完毕")
            if callback:callback(avatar_string)
        except Exception as e:
            print(f"callback解析事件数据失败：{str(e)}\n再次生成：")
            Avatar_Proactive(prompt_Writer.Image_Prompt_Writer)
    
    settings.passive_dial_manager.user_input_send(prompt,callback=Avatar_Proactive_callback)

def display_Avatar_response(Avatar_response: List[AvatarResObject], output_format: str = "string",output_file:Optional[str]=None) -> Optional[str]:
    """
    显示 Avatar 的响应内容。
    :param Avatar_response: AvatarResObject 的列表，包含响应内容和用户选择。
    :param output_format: 输出格式，支持 "console"（默认）和 "string"。
    :return: 如果 output_format 是 "string"，返回格式化的字符串；否则返回 None。
    """
    output = []
    content = ""
    for response in Avatar_response:
        # 添加响应类型和内容
        output.append(f"响应类型: {response.respond_type}")
        output.append(f"内容: {response.respond}")
        content += f"响应类型: {response.respond_type}\n"
        content += f"内容: {response.respond}\n"
        # 如果有用户选择，添加用户选择的选项
        if response.user_choice:
            output.append("用户选择选项：")
            content += f"用户选择选项：\n"
            for choice in response.user_choice:
                for key, value in choice.items():
                    output.append(f"  {key}: {value}")
                    content += f"  {key}: {value}\n"
        
        # 添加分隔线
        output.append("-" * 30)
        content += "-" * 30 +"\n"
    if output_file:
        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        timeRecord = f"\nAvatar模拟回应 创建时间:{formatted_time}\n"
        save_to_file(output_file,timeRecord,"a")
        save_to_file(output_file,content,"a")


    # 根据输出格式返回结果
    formatted_output = "\n".join(output)
    if output_format == "console":
        print(formatted_output)
        return None
    elif output_format == "string":
        return formatted_output
    else:
        raise ValueError("Unsupported output format. Use 'console' or 'string'.")