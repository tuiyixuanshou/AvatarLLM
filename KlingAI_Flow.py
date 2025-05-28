from prompt_Writer import AvatarImageVideoGenerator
import KlingAPI
from tools import save_to_file,load_prompt
import settings
import Image_Generation


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

        def video_prompt_ready(video_prompt_text):
            KlingAPI.Kling_API_Video(video_prompt_text, image_url)

        if settings.IS_VIDEO:
            print("开始生成视频：")
            generator.generate_video_prompt(image_url,cur_avatar_respond, video_prompt_ready)
        else:
            if settings.WEEK_INDEX<=3:
                settings.WEEK_INDEX = settings.WEEK_INDEX+1
                #Avatar_Driven_Respond.Avatar_Proactive(prompt_Writer.Image_Prompt_Writer)
                Image_Generation.Avatar_Proactive_Image()
            else:
                print("结束生成")


    else:
        print("图片生成失败，无法生成视频。")

def video_generate_callback(video_url):
    if video_url:
        print(f"Generated Image URL: {video_url}")
        save_to_file("Avatar_Story.txt",video_url+"\n","a")
        # if settings.WEEK_INDEX<=3:
        #     settings.WEEK_INDEX = settings.WEEK_INDEX+1
        #     #Avatar_Driven_Respond.Avatar_Proactive(prompt_Writer.Image_Prompt_Writer)
        #     Image_Generation.Avatar_Proactive_Image()
        # else:
        #     print("结束生成")


def single_Video_Generation():

    def video_prompt_ready(video_prompt_text):
            KlingAPI.Kling_API_Video(video_prompt_text, load_prompt("Avatara_Partical.txt"),callback=video_generate_callback)

    generator.generate_Singlevideo_prompt("None",video_prompt_ready)   

  
# 示例调用
if __name__ == "__main__":
    #avatar_respond = "我今天在图书馆自习，准备参加下周的期末考试。"  # 示例输入
    #main_generation_flow(avatar_respond)
    single_Video_Generation()