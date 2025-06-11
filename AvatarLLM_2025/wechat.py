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

from openai import OpenAI

def llm_reply(conversation_history):
        client = OpenAI(api_key="sk-0e5049d058f64e2aa17946507519ac53", base_url="https://api.deepseek.com")
        sys_msg = []
        if isinstance(conversation_history, list) and conversation_history:
            for idx, _info in enumerate(conversation_history):
                if idx < max(0,len(conversation_history)-10):
                    continue
                is_last = (idx == len(conversation_history) - 1)
                if '@AI@:' in _info:
                    _info = _info.replace('@AI@:', '')
                    sys_msg.append({
                        "role": "assistant",
                        "content": _info
                    })
                else:
                    if is_last:
                        sys_msg.append({
                            "role": "user",
                            "content": _info + "(尽量参考最近几轮对话，简短回答，不超过30个字)"
                        })
                    else:
                        sys_msg.append({
                            "role": "user",
                            "content": _info
                        })
        response = client.chat.completions.create(
            model="deepseek-chat",
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

    for i, msg in enumerate(messages):
        name = msg.Name.strip()
        if not name:
            continue

        if name == '以下为新消息':
            continue

        rect = msg.BoundingRectangle
        if not rect:
            continue

        # 跳过时间戳类
        if re.match(r'\d{1,2}:\d{2}|\d{4}年\d{1,2}月\d{1,2}日', name):
            continue

        result.append(name)

    return result

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
                    # 反复滚动几次，加载旧消息
                    for _ in range(2):
                        message_list.WheelUp()
                        time.sleep(0.1)
                    for _ in range(2):
                        message_list.WheelDown()
                        time.sleep(0.1)

                    messages = extract_message(message_list)
                    if messages:
                        #等待5秒种用户没输入就开始生成回答
                        wait_acc = 0
                        for iter in range(0,5):
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

                        init = False
                        if nickname not in conversation_history:
                            conversation_history[nickname] = []
                            new_conversation_msg_state[nickname] = True
                            init = True
                        info = ''
                        if init:
                            # 第一次初始化阶段，按照新消息的提示信息来获取所有信息
                            last_msg = messages[-message_count::]
                            for msg in last_msg:
                                conversation_history[nickname].append(msg)
                        else:
                            # 看历史中有多少消息没记录下来
                            first_str = conversation_history[nickname][0]
                            index = 0
                            for msg in messages:
                                if msg == first_str:
                                    break
                                else:
                                    index += 1
                            iter = 0
                            for msg in messages:
                                if iter < index:
                                    iter += 1
                                    continue
                                if (msg not in conversation_history[nickname]) and ("@AI@:"+msg not in conversation_history[nickname]): 
                                    conversation_history[nickname].append(msg)
                        #print("conversation_history --------------------------------------------------")
                        #print(conversation_history[nickname])
                        #print("--------------------------------------------------")
                        out_info = llm_reply(conversation_history[nickname])
                        conversation_history[nickname].append("@AI@:"+out_info)
                        
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
            watch_list = ['A晶','24研 信息设计 秦菲儿']  # 你的监听名单
            check_new_messages(wechat_win, watch_list)
        except KeyboardInterrupt:
            print("👋 已手动退出监听")
        except Exception as e:
            print(f"❌ 程序异常退出：{e}")