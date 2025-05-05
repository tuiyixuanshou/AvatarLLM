from prompt_Writer import AvatarImageVideoGenerator
import KlingAPI
from tools import save_to_file

generator = AvatarImageVideoGenerator()
cur_avatar_respond = ""

def main_generation_flow(avatar_respond):
    cur_avatar_respond = avatar_respond
    def image_prompt_ready(prompt_text):
        KlingAPI.Kling_API_Image(prompt_text, callback=image_generated_callback)

    generator.generate_image_prompt(avatar_respond, image_prompt_ready)

def image_generated_callback(image_url):
    if image_url:
        print(f"Generated Image URL: {image_url}")
        save_to_file("Avatar_Story.txt",image_url+"\n","a")
        print("开始生成视频：")

        def video_prompt_ready(video_prompt_text):
            KlingAPI.Kling_API_Video(video_prompt_text, image_url)

        generator.generate_video_prompt(image_url,cur_avatar_respond, video_prompt_ready)
    else:
        print("图片生成失败，无法生成视频。")
    
# 示例调用
if __name__ == "__main__":
    avatar_respond = "我今天在图书馆自习，准备参加下周的期末考试。"  # 示例输入
    main_generation_flow(avatar_respond)