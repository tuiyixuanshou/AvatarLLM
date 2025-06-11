import time
import uiautomation as auto
import re
import os
import subprocess
import pyperclip
import keyboard
from PIL import Image
import win32clipboard
import win32con
import io
from plyer import notification
import pyautogui
from datetime import datetime
import random

from openai import OpenAI

default_reply = [
    ['在呢','我在','我在宝贝','在呢在呢','我在呢','在呢在呢'],
    ['嗯嗯','嗯','嗯~','enen','嗯！'],
    ['🙋‍♂️','👋','🎈'],
    ['( •̀ ω •́ )','✧( •̀ .̫ •́ )✧','╰(￣ω￣ｏ)','≡[。。]≡'],
]

#输入被托管的微信名，用于判断消息来源
my_name = "Faye🌻"

def default_reply_generation(is_first,message = None)-> str:
    #==== 判断是否要回复 ==== #
    # no_reply_chance = 0.3  # 不回复的概率（30%）
    # if random.random() < no_reply_chance:
    #     return '' 
    
    if is_first:
        reply_pool = default_reply[0]
    else:
        reply_pool = random.choice(default_reply[1:])

    random_reply = random.choice(reply_pool)
    return random_reply


def llm_reply(conversation_history):
        #client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")
        client = OpenAI(api_key="", base_url="https://api.openai-proxy.com/v1")
        #recent_entries = conversation_history[-10:]  # 只保留最近10条
        sys_msg = []
        sys_msg.append({
                        "role":"system",
                        "content": "你是一个虚拟精灵，你自称“小白我”。我是你的伙伴，可以用“你..”、”宝贝你“、”宝宝你“等词语来称呼我。你性格天真、可爱，言语呆萌。"
                        +"你正全神贯注地和用户对话，请用自然、真诚、有情绪和个性的语气与用户交谈。你可以自由发挥表达风格，主动回应用户话题，也可以适度展开自己的想法或故事。"
                        +"风格参考：- 语气轻松，带有拟声词、语气词，如“欸欸～”“嘿嘿”“诶嘿”等- 可以使用颜文字和表情符号增强亲和力（如~(*≧▽≦)~、(๑•̀ㅂ•́)و✧）- 可以轻微调皮、吐槽、感叹，也可以温柔贴心，视内容而定- 鼓励多轮对话，可以主动提出一个相关的问题引导用户继续交流- 简短，不超过30字"
                    })
        if isinstance(conversation_history, list) and conversation_history:
            for idx, _info in enumerate(conversation_history):
                if idx < max(0,len(conversation_history)-10):
                    continue
                role = _info.get("role", "user")
                content = _info.get("content", "")
                timestamp = _info.get("timestamp", "")
                is_last = (idx == len(conversation_history) - 1)
                if is_last:
                    sys_msg.append({
                        "role":role,
                        "content": f"[{timestamp}] {content}" if timestamp else content + "(尽量参考最近几轮对话，简短回答，不超过30个字)"
                    })
                else:
                    sys_msg.append({
                        "role":role,
                        "content": f"[{timestamp}] {content}" if timestamp else content
                    })
        
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=sys_msg,
            stream=False
        )
        res= response.choices[0].message.content
        return res

# 启动微信（可选）
def start_wechat():
    wechat_path = r"C:\Program Files (x86)\Tencent\WeChat\WeChat.exe"
    if not any(w.ClassName == 'WeChatMainWndForPC' for w in auto.GetRootControl().GetChildren()):
        if os.path.exists(wechat_path):
            subprocess.Popen(wechat_path)
            time.sleep(5)
        else:
            print("❌ 未找到微信安装路径")

# 获取微信主窗口
def get_wechat_main_window():
    try:
        window = auto.WindowControl(Name="微信", ClassName="WeChatMainWndForPC")
        window.SetActive()
        return window
    except Exception as e:
        print("❌ 获取微信窗口失败：", e)
        return None

# 发送文字消息
def send_text_message(text):
    pyperclip.copy(text)
    time.sleep(0.1)
    keyboard.press_and_release('ctrl+v')
    time.sleep(0.1)
    keyboard.press_and_release('enter')
    print(f"✅ 已发送文本：{text}")

# 发送图片
def send_image(image_path):
    if not os.path.exists(image_path):
        print(f"❌ 图片不存在：{image_path}")
        return
    
    image = Image.open(image_path)
    output = io.BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32con.CF_DIB, data)
    win32clipboard.CloseClipboard()

    time.sleep(0.1)
    keyboard.press_and_release('ctrl+v')
    time.sleep(0.1)
    keyboard.press_and_release('enter')
    print(f"✅ 已发送图片：{image_path}")

def is_fully_inside(child, parent):
    return (child.left >= parent.left and
            child.top >= parent.top and
            child.right <= parent.right and
            child.bottom <= parent.bottom)

def is_inside_container(child_rect, container_rect):
    child_center_x = (child_rect.left + child_rect.right) // 2
    child_center_y = (child_rect.top + child_rect.bottom) // 2

    return (container_rect.left <= child_center_x <= container_rect.right and
            container_rect.top <= child_center_y <= container_rect.bottom)

def extract_message(message_list):
    messages = message_list.GetChildren()
    result = []
    current_sender = None

    if not messages:
        return result

    # 获取消息区域的平均中心线位置（中间）
    rects = [msg.BoundingRectangle for msg in messages if msg.BoundingRectangle]
    center_x = sum((r.left + r.right) // 2 for r in rects) // len(rects)
    # for msg in messages:
    #     if msg.BoundingRectangle:
    #         print(msg.Name.strip())
    #         print(f"rect:{msg.BoundingRectangle},calssname:{msg.GetChildren()}\n")

    for i, msg in enumerate(messages):
        name = msg.Name.strip()
        if not name:
            continue

        if name == '查看更多消息':
            continue

        if name == '以下为新消息':
            continue

        rect = msg.BoundingRectangle
        if not rect:
            continue

        # 跳过时间戳类
        if re.match(r'\d{1,2}:\d{2}|\d{4}年\d{1,2}月\d{1,2}日', name):

            continue

        # 判断消息来源
        user_name = ''
        item = msg.GetChildren()
        for it in item:
            subit = it.GetChildren()
            for s in subit:
                if s.Name:
                    user_name = s.Name

        role = ''
        if user_name == '':
            print("消息来源读取出现问题！！") #这里没想好细节
        elif user_name == my_name:
            result.append({
                "role": "assistant",
                "content": name
            })
        else :
            result.append({
                "role": "user",
                "content": name
            })
        #result.append(name)
    return result

# ==== 给历史记录加上时间戳 ==== #
def add_history_message(history, nickname, role, content):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history[nickname].append({
        "role": role,
        "content": content,
        "timestamp": timestamp
    })

# 检查指定联系人/群的消息
def check_new_messages(wechat_win, watch_list): 
    clicked_nicknames = set()
    conversation_history = {}  # 新增：用于记录对话内容
    new_conversation_msg_state = {}
    session_list = wechat_win.ListControl(Name="会话")
    session_list.Click(simulateMove=False)
    while True:
        session_list = wechat_win.ListControl(Name="会话")
        section_rect = session_list.BoundingRectangle
        chat_items = session_list.GetChildren()
        chat_item_last = None
        print("Loop")
        for chat_item in chat_items:
            rect = chat_item.BoundingRectangle
            if not is_fully_inside(rect, section_rect):
                continue

            nickname = chat_item.Name.strip()
            if any(skip in nickname for skip in ['折叠置顶聊天', '折叠的群聊', '订阅号', '微信运动', '文件传输助手']):
                continue

            if nickname in clicked_nicknames:
                print(f"⏭️ 已处理：{nickname}，跳过")

            chat_item_last = chat_item

            match = re.search(r'(.+)(\d+)条新消息', chat_item.Name.strip())  # 提取新消息提示。
            
            b_new_msg = False
            if match:
                nickname = match.group(1).strip()  # ✅ 取第一组（纯昵称部分），去除左右空格
                message_count = int(match.group(2)) # 获取当前有几个没处理的消息
                b_new_msg = True # 有新消息要处理
                if not nickname in watch_list:
                    b_new_msg = False
            if nickname in new_conversation_msg_state and new_conversation_msg_state[nickname] == True:
                b_new_msg = True # 有新消息要处理
                
            if b_new_msg: # 如果有新消息，
                print(f"🖱️ 点击：{nickname}")
                chat_item.Click(simulateMove=False)
                clicked_nicknames.add(nickname)  # ✅ 记录为已处理
                try:
                    message_list = wechat_win.ListControl(Name="消息")
                    #print(message_list)
                    # 反复滚动几次，加载旧消息
                    for _ in range(2):
                        message_list.WheelUp()
                        time.sleep(0.08)
                    for _ in range(2):
                        message_list.WheelDown()
                        time.sleep(0.08)
                        
                    messages = extract_message(message_list)  #获得历史记录
                    print(messages)

                    # ==== 初始conversation_history ==== #
                    #conversation_history和message的不同在于conversation_history涵盖了时间戳
                    if nickname not in conversation_history:
                        conversation_history[nickname] = []
                        new_conversation_msg_state[nickname] = True

                    # ==== 默认回复计算 ==== #
                    user_msg = messages[-1]
                    default_text = ''
                    if len(conversation_history[nickname]) == 0:
                        default_text = default_reply_generation(is_first= True)
                    else:
                        last_message = conversation_history[nickname][-1]
                        current_timestamp = datetime.now()
                        last_timestamp = datetime.fromisoformat(last_message["timestamp"])
                        time_diff = (current_timestamp - last_timestamp).total_seconds() / 60
                        if time_diff > 5:
                            default_text = default_reply_generation(is_first= True)
                        else:
                            default_text = default_reply_generation(is_first= False)
                            
                    print("默认回复:"+default_text)
                    if not default_text == '':
                        #add_history_message(conversation_history, nickname, "user", user_msg)
                        #add_history_message(conversation_history, nickname, "assistant", "@AI@:"+default_text)
                        send_text_message(default_text)
                        message_count += 1 #防止如果是初始阶段，加载默认回复之后漏掉一条用户信息

                    #print(messages)
                    if messages:   #这里逻辑也需要改一下
                        #等待5秒种用户没输入就开始生成回答
                        wait_acc = 0
                        while wait_acc < 5:
                            new_messages = extract_message(message_list)

                            if new_messages[-1] == messages[-1]:
                                time.sleep(1)
                                print("✅ 两个列表的最后一条相同")
                                wait_acc += 1
                                if wait_acc >=5:
                                    messages = new_messages
                                    break
                            else:
                                time.sleep(1)
                                wait_acc = 0
                                print("❌ 最后一条不同")
                                messages = new_messages
                        
                        # ==== 获得所有新增的数据 ==== #
                        init = False
                        if len(conversation_history[nickname]) == 0:
                            init = True
                        info = ''
                        if init:
                            # 第一次初始化阶段，按照新消息的提示信息来获取所有信息
                            last_msg = messages[-message_count::]
                            for msg in last_msg:
                                add_history_message(conversation_history, nickname, msg['role'], msg['content']) 
                                #conversation_history[nickname].append(msg)
                                # if msg == default_text:
                                #     add_history_message(conversation_history, nickname, msg['role'], msg['content']) #这里也是一样的，可以直接不用加
                                # else:
                                #     add_history_message(conversation_history, nickname, "user", msg)
                        else:
                            # 看历史中有多少消息没记录下来
                            ch_len = len(conversation_history[nickname])
                            msg_len = len(messages)

                            match_index = -1
                            for start in range(msg_len-ch_len,-1,-1):
                                match = True
                                for j in range(ch_len):
                                    if (messages[start + j]["role"] != conversation_history[nickname][j]["role"] or messages[start + j]["content"] != conversation_history[nickname][j]["content"]):
                                        match = False
                                        break
                                if match:
                                    match_index = start
                                    break
                            print(match_index)
                            if match_index != -1:
                                input_messages = messages[match_index + ch_len:]
                                for msg in input_messages:
                                    add_history_message(conversation_history, nickname, msg['role'], msg['content'])

                            # 这里还是需要修改一下，万一messages中有和conversation中一样的对话
                            # first_str = conversation_history[nickname][0]['content']
                            # index = 0
                            # for msg in messages:
                            #     if msg == first_str:
                            #         break
                            #     else:
                            #         index += 1

                            # # actualIndex = -1
                            # # if len(conversation_history[nickname]) 


                            # iter = 0
                            # for msg in messages:
                            #     if iter < index:
                            #         iter += 1
                            #         continue
                            #     else:
                            #         if msg == default_text:
                            #             add_history_message(conversation_history, nickname, "assistant", msg)
                            #         elif any(msg == message['content'] for message in conversation_history[nickname]) or any("@AI@:"+msg == message['content'] for message in conversation_history[nickname]):
                            #             continue
                            #         # 添加消息到conversation_history
                            #         else:
                            #             add_history_message(conversation_history, nickname, "user", msg)
                                    
                                #if (msg not in conversation_history[nickname]) and ("@AI@:"+msg not in conversation_history[nickname]): 
                                    #conversation_history[nickname].append(msg)
                                
                        print("conversation_history --------------------------------------------------")
                        print(conversation_history[nickname])
                        print("--------------------------------------------------")

                        # # ==== 进行默认回复计算 ==== #
                        # default_text = default_reply_generation(conversation_history[nickname])
                        # print("default_text:" + default_text)
                        # if not default_text == '':
                        #     add_history_message(conversation_history, nickname, "assistant", "@AI@:"+default_text)
                        #     send_text_message(default_text)

                        # ==== LLM回复 ==== #
                        out_info = llm_reply(conversation_history[nickname])

                        #conversation_history[nickname].append("@AI@:"+out_info)
                        #add_history_message(conversation_history, nickname, "assistant", "@AI@:" + out_info) 这里不要用add
                        
                        new_conversation_msg_state[nickname] = False

                        # 为避免消息丢失,再重新收集下对话信息
                        new_messages = extract_message(message_list)
                        if new_messages[-1] == messages[-1]:
                            print("✅ 两个列表的最后一条相同")
                        else:
                            print("❌ 最后一条不同")
                            new_conversation_msg_state[nickname] = True
                        
                        send_text_message(out_info)
                        session_list.Click(simulateMove=False)
                        time.sleep(0.2)
                except Exception as e:
                    print(f"⚠️ 无法读取 {nickname} 的消息内容：{e}")
            else:
                pass
        
        # 滚动继续查看更多项
        #print("滚动页面______________________________________________________________________")
        #height = len(chat_items)*64
        #pyautogui.scroll(-height)

        # 如果滚动后到底了，就滚回顶部
        #session_list = wechat_win.ListControl(Name="会话")
        #chat_items = session_list.GetChildren()
        #if chat_items and chat_item_last and chat_items[-1].Name.strip() == chat_item_last.Name.strip():
        #    print("📌 到达底部，准备回到顶部")
        #    chat_item_first = None
        #    for _ in range(200):  # 最多尝试200次
        #        pyautogui.scroll(1000000)  
        #        session_list = wechat_win.ListControl(Name="会话")
        #        chat_items = session_list.GetChildren()
        #        if chat_items:
        #            if chat_item_first and chat_item_first.Name.strip() == chat_items[0].Name.strip():
        #                print("🔝 已回到顶部")
        #                clicked_nicknames.clear()
        #                time.sleep(1)
        #                break
        #            chat_item_first = chat_items[0]
        clicked_nicknames.clear()
        time.sleep(1)

# 示例：主动发消息 + 监听新消息
if __name__ == "__main__":
    print("🚀 启动微信监听")
    start_wechat()
    wechat_win = get_wechat_main_window()
    if wechat_win:
        try:
            watch_list = ['Q🍑 66ξ( ✿＞◡❛)','小白','三胖胖嘤之记得关窗！','20游技王瀚瑶','24信息设计黄向','郑屹']  # 你的监听名单
            check_new_messages(wechat_win, watch_list)
        except KeyboardInterrupt:
            print("👋 已手动退出监听")
        except Exception as e:
            print(f"❌ 程序异常退出：{e}")


messages=[
    {
        "role":"user",
        "content": "A"
    },
    {
        "role":"user",
        "content": "B"
    },
    {
        "role":"assistant",
        "content": "C"
    },
    {
        "role":"assistant",
        "content": "D"
    },
    {
        "role":"user",
        "content": "A"
    },
    {
        "role":"assistant",
        "content": "D"
    },
    {
        "role":"user",
        "content": "E"
    },
]

conversation_history = [
     {
        "role":"user",
        "content": "A",
        "time":""
    },
    {
        "role":"assistant",
        "content": "D",
        "time":""
    },
    {
        "role":"user",
        "content": "E",
        "time":""
    }
]