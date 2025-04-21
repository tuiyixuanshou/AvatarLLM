import LLM_Manager
import settings
import json
import Avatar_Driven_module
import Avatar_Driven_Respond
import prompt_Writer

if __name__ == "__main__":

    def _Passive_Dial_Callback(response,error):
        if error:
            print(f"被动对话回调出现错误：{error}")
        else:
            print("AI回复:",response)

    print("生成目标：\n")
    settings.M_Avatar_Target.generate_targets()
    print("生成事件：\n")
    #回调链
    # # lambda_TargetWeigh_callback = lambda: M_Avatar_Target.APlan_TargetWeigh(M_Avatar_Event.exposed_events)
    # M_Avatar_Event.generate_event(callback = lambda_TargetWeigh_callback)
    def generate_event_callback():
        settings.M_Avatar_Target.APlan_TargetWeigh(settings.M_Avatar_Event.exposed_events,callback=generate_plan_callback)
    def generate_plan_callback():
        settings.M_Avatar_Target.APlan_SpecifyPlan(settings.M_Avatar_Target.target, settings.M_Avatar_Target.weights)
    settings.M_Avatar_Event.generate_event(callback=generate_event_callback)

    #Prompt_Writer
    

    #被动回复,长期监听
    while True:
        if not settings.passive_dial_manager.is_ai_running:
            user_input = input("用户输入:")
            if user_input.lower() == "exit":
                break
            else:
                if(user_input.lower() == "test"):
                    Avatar_Driven_Respond.Avatar_Proactive(prompt_Writer.Image_Prompt_Writer)
                else:
                    response = settings.passive_dial_manager.user_input_send(user_input,_Passive_Dial_Callback)
