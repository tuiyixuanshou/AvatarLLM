import random
import re
import numpy as np

import Emotion
import Dialog
import Memory
import Calendar
import World_Plan

class VirtualAgent:
    def __init__(self, personality, emotional_vector, behavior_library):
        print("\n\n\n\n\n")
        print(f"\n🤖 Avatar创建--------------------------------------------")
        print("个性数值:" + str(personality))
        print("情绪数值:" + str(emotional_vector))

        self.gender = "男"
        self.personality = personality
        self.behavior_library = behavior_library
        self.bio_energy = 1.0 # 体力
        self.bps_state_vector = personality # BPS需求向量
        self.behavior_fatigue = {}  # 记录每个行为的倦怠值 ∈ [0, 1]
        
        self.emotion_module = Emotion.EmotionState(personality,emotional_vector) # 添加情绪模块
        self.dialogue_module = Dialog.DialogModule(self) # 添加对话模块
        self.memory_module = Memory.MemoryModule(self,20) # 添加记忆模块
        self.calendar_module = Calendar.Calendar(self) # 添加日历模块
        self.external_event_manager = World_Plan.ExternalEventManager("M_file/External_Event.json")

    def reset_state(self):
        self.bio_energy = 1.0 # 体力
        self.emotion_module.valence = self.emotion_module.valence_baseline  # 让情绪回到偏向值
        self.emotion_module.arousal = 0.5
        self.emotion_module.frustration_level = 0.0
        self.emotion_module.mood_history = []
        self.behavior_fatigue = {}

    def gen_calender(self):
        print(f"\n🎯 每日计划生成开始-------------------------------------------------")
        for day in range(3):
            print(f"\n📅 Day {day}: {self.calendar_module.calendar[day]['date']} {self.calendar_module.calendar[day]['weekday']} -------------------------------------------------")
            for Time_slot in ["morning", "afternoon", "evening"]:
                self.calendar_module.prepare_calendar(day,Time_slot)
            self.daily_update()
        
        print(f"\n🎯 每日计划生成结束，Avatar开始生成执行细节-------------------------------------------------")
        self.reset_state() #重置虚拟人状态
        self.external_event_manager.save_External_event_init() #重置外部事件库
        for day in range(3):
            print(f"\n📅 Day {day}: {self.calendar_module.calendar[day]['date']} {self.calendar_module.calendar[day]['weekday']} -------------------------------------------------")
            for Time_slot in ["morning", "afternoon", "evening"]:
                self.calendar_module.play_calendar(day,Time_slot)
            self.daily_update()
        print(f"\n🎯 计划生成结束。开始进行对话-------------------------------------------------")

    def apply_behavior_feedback(self, behavior_name, success_value):
        behavior = self.behavior_library[behavior_name]

        # 获取行为权重匹配度
        bio_require = np.array(behavior["bio_require"])
        bio_cunsumption = np.array(behavior["bio_cunsumption"])
        bio_motivation = max(0.0, bio_cunsumption)

        psycho_cunsumption = np.array(behavior["psycho_cunsumption"])
        psycho_motivation = max(0.0, psycho_cunsumption)

        bio_weight = np.array(behavior["Weight"])[:3]
        psycho_social_weight = np.array(behavior["Weight"])[3:]
        norm_bio_weight = np.linalg.norm(bio_weight)
        norm_psycho_social_weight = np.linalg.norm(psycho_social_weight)

        personality1_bio_weight = self.personality[:3]
        personality1_psycho_social_weight = self.personality[3:]
        norm_personality_bio_weight = np.linalg.norm(personality1_bio_weight)
        norm_personality1_psycho_social_weight = np.linalg.norm(personality1_psycho_social_weight)

        state_bio_weight = self.bps_state_vector[:3]
        state_psycho_social_weight = self.bps_state_vector[3:]

        dot_bio_weight = np.dot(state_bio_weight, bio_weight) / (norm_personality_bio_weight * norm_bio_weight)
        dot_psycho_social_weight = np.dot(state_psycho_social_weight, psycho_social_weight) / (norm_personality1_psycho_social_weight * norm_psycho_social_weight)

        # 生理/心理反馈
        bio_cunsumption = np.array(behavior["bio_cunsumption"])
        psycho_cunsumption = np.array(behavior["psycho_cunsumption"])

        # 若成功：直接按比例加减
        # 若失败：放大负面反馈（消耗更大）
        success_value = np.clip(success_value,-1.0,1.0)

        if success_value > 0.0:
            if psycho_cunsumption > 0.0:
                psycho_cunsumption = abs(psycho_cunsumption) * abs(success_value)
            else:
                psycho_cunsumption = abs(psycho_cunsumption) * (1.0-abs(success_value)) # 成功降低了消耗感
        else:
            if psycho_cunsumption > 0.0:
                psycho_cunsumption = -abs(psycho_cunsumption)  * abs(success_value) # 失败带来了挫败感
            else:
                psycho_cunsumption = -abs(psycho_cunsumption) * abs(success_value)

        if bio_cunsumption > 0.0:
            self.bio_energy = np.clip(self.bio_energy + bio_cunsumption * dot_bio_weight * (success_value + 1.0) * 0.5, 0.0, 2.0)
        else:
            self.bio_energy = np.clip(self.bio_energy + bio_cunsumption * dot_bio_weight * (1.0 - success_value) * 0.5, 0.0, 2.0)

        # 倦怠调节（仅当行为执行了，无论成功与否）
        repeat_tolerance_score = self.bps_state_vector[5] * 0.4 + self.bps_state_vector[4] * 0.2 + self.bps_state_vector[10] * 0.2 + self.bps_state_vector[7] * 0.1 - self.bps_state_vector[3] * 0.1
        repeat_tolerance_score = np.clip(repeat_tolerance_score, 0.0, 1.0)
        repeat_tolerance_score *= dot_psycho_social_weight
        self.behavior_fatigue[behavior_name] = min(1.0, self.behavior_fatigue.get(behavior_name, 0) + 0.2 * (1.0 - repeat_tolerance_score))

        # 情绪反馈：调用情绪状态更新
        self.emotion_module.process_behavior(self.bio_energy, behavior, psycho_cunsumption * dot_psycho_social_weight, success_value)


    def daily_update(self):
        # 生理值/心理值/情绪 每天恢复
        self.bio_energy = np.clip(self.bio_energy * 0.8 + 0.2, 0.0, 2.0)
        self.emotion_module.valence = np.clip(self.emotion_module.valence * 0.2 + self.emotion_module.valence_baseline * 0.8, -1, 1.0)
        self.emotion_module.arousal = np.clip(self.emotion_module.arousal * 0.2 + 0.5 * 0.8, 0.0, 1.0)

        # 行动的倦怠值每日衰减
        for name in self.behavior_fatigue:
            self.behavior_fatigue[name] = max(0.0, self.behavior_fatigue[name] - 0.05)

    def _softmax(self, x, temperature=1.0):
        x = np.array(x)
        x = x / temperature  # 控制选择的“激进程度”：越小越接近贪婪，越大越平均
        e_x = np.exp(x - np.max(x))  # 防止溢出
        return e_x / e_x.sum()
    
    def _select_behavior(self, current_Time_slot="morning",life_style_weight = None):
        scores = {}
        dynamic_choice_bias = 1.0
        self.emotion_module.decay()
        for name, content in self.behavior_library.items():
            if "Time" in content and current_Time_slot not in content["Time"]:
                continue

            bio_require = np.array(content["bio_require"])
            if bio_require > self.bio_energy:
                continue

            if life_style_weight is not None:
                # ==== 动态 choice_bias，根据当天tag权重调节 ====
                tag = np.array(content.get("tag", [1,0,0,0,0]))  # 获取事件标签
                tag_weight_score = float(np.dot(tag, life_style_weight))  # 计算事件tag与当天活动权重的点积
                original_choice_bias = content.get("choice_bias", 1.0)
                dynamic_choice_bias = original_choice_bias * tag_weight_score


            # ==== 计算行动与人物BPS的匹配度 ====
            bio_cunsumption = np.array(content["bio_cunsumption"])
            bio_motivation = max(0.0, bio_cunsumption)

            psycho_cunsumption = np.array(content["psycho_cunsumption"])
            psycho_motivation = max(0.0, psycho_cunsumption)

            bio_weight = np.array(content["Weight"])[:3]
            psycho_social_weight = np.array(content["Weight"])[3:]
            norm_bio_weight = np.linalg.norm(bio_weight)
            norm_psycho_social_weight = np.linalg.norm(psycho_social_weight)

            personality1_bio_weight = self.personality[:3]
            personality1_psycho_social_weight = self.personality[3:]
            norm_personality_bio_weight = np.linalg.norm(personality1_bio_weight)
            norm_personality1_psycho_social_weight = np.linalg.norm(personality1_psycho_social_weight)

            state_bio_weight = self.bps_state_vector[:3]
            state_psycho_social_weight = self.bps_state_vector[3:]

            dot_bio_weight = np.dot(state_bio_weight, bio_weight) / (norm_personality_bio_weight * norm_bio_weight)
            dot_psycho_social_weight = np.dot(state_psycho_social_weight, psycho_social_weight) / (norm_personality1_psycho_social_weight * norm_psycho_social_weight)

            fatigue = self.behavior_fatigue.get(name, 0.0)
            fatigue_factor = pow(max(0.0, min(1.0, 1.0 - fatigue)), 0.25)

            # ==== 添加情绪影响 ====
            emotion_modifier = 1.0 + 0.25 * self.emotion_module.valence + 0.25 * (self.emotion_module.arousal - 0.5)
            emotion_modifier = np.clip(emotion_modifier, 0.75, 1.25)

            # ==== 抗拒因子（含情绪）====
            physical_resistance = pow(np.clip(self.bio_energy + bio_motivation * 0.5, 0.0, 1.0), 0.5) * emotion_modifier
            mental_resistance = pow(np.clip((self.emotion_module.valence*0.5+0.5) + psycho_motivation * 0.5, 0.0, 1.0), 0.5) * emotion_modifier

            # ==== 行为最终得分 ====
            if life_style_weight is not None:
                choice_bias = dynamic_choice_bias
            else:
                choice_bias = content.get("choice_bias", 1.0)
            bio_score = dot_bio_weight * choice_bias * fatigue_factor * physical_resistance
            psycho_social_score = dot_psycho_social_weight * choice_bias * fatigue_factor * mental_resistance

            score = (bio_score * (1.0 - self.bio_energy) + psycho_social_score * self.bio_energy) # 马斯洛 理论当生理能量不足时，更需要补充基本能量
            #score *= frustration_modifier  # 应用沮丧调节

            scores[name] = score

        return scores
    
    def _extract_all_strings(self, nested_data, prefix=""):
        """
        递归提取嵌套结构中所有的字符串，并带上键路径前缀（如 动画类 - 日漫动画 - 千与千寻）
        """
        results = []

        if isinstance(nested_data, str):
            results.append(f"{prefix}-{nested_data}" if prefix else nested_data)

        elif isinstance(nested_data, list):
            for item in nested_data:
                results.extend(self._extract_all_strings(item, prefix))

        elif isinstance(nested_data, dict):
            for key, value in nested_data.items():
                new_prefix = f"{prefix}-{key}" if prefix else key
                results.extend(self._extract_all_strings(value, new_prefix))

        return results

    def _apply_behavior(self, chosen_behavior, success_rate=0.5):

        match = re.search(r'【(.*?)】', chosen_behavior)
        if match:
            inner = match.group(1)
            outer = re.sub(r'【.*?】', '', chosen_behavior)
            chosen_behavior = outer.strip()
            selected_detail = inner.strip()
        else:
            chosen_behavior = chosen_behavior.strip()
            selected_detail = ''  # 没有括号内容时返回原始文本和空串
    
        # 随机生成行为成功与否（成功率可由匹配度决定，或者恒定90%）
        success = random.random() < success_rate
        if success:
            success = random.random() # 转为 0～1
        else:
            success = -random.random() #转为 -1～0

        for_user = self.behavior_library[chosen_behavior].get("for_user", 0.0)
        if for_user == 1.0:
            success = 1.0

        # 执行行为反馈并更新情绪
        self.apply_behavior_feedback(chosen_behavior, success_value=success)

        if selected_detail == '':
            # 获取该行为的配置数据
            behavior_data = self.behavior_library.get(chosen_behavior, {})
            details = behavior_data.get("Detail", [])

            # 递归提取所有可选字符串项
            all_items = self._extract_all_strings(details)
            selected_detail = random.choice(all_items) if all_items else "健步走"

        if success > 0.5:
            success = "实现目标"
        elif success > 0.25:
            success = "进展顺利"
        elif success > 0.0:
            success = "小有收获"
        elif success > -0.25:
            success = "情况不妙"
        elif success > -0.5:
            success = "状况堪忧"
        else:
            success = "惨遭失败"

        if for_user == 1.0:
            return chosen_behavior + "【" + selected_detail + "】", "进展顺利"
        else:
            return chosen_behavior + "【" + selected_detail + "】", success

    def select_best_behavior(self, top_k=3, current_Time_slot="morning",life_style_weight=None, Softmax=True, temperature=1.0):
        scores = self._select_behavior(current_Time_slot,life_style_weight)

        # 选择 Top-K
        if not scores:
            return None, {}
        top_behaviors = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        names, raw_scores = zip(*top_behaviors)

        if Softmax:
            # 计算 Softmax 概率
            probabilities = self._softmax(raw_scores, temperature=temperature)
            chosen_behavior = random.choices(names, weights=probabilities, k=1)[0]
        else:
            # 计算 平均 概率
            total_score = sum(raw_scores)
            probabilities = [v / total_score for v in raw_scores] if total_score > 0 else [1 / len(raw_scores)] * len(raw_scores)
            chosen_behavior = random.choices(names, weights=probabilities, k=1)[0]

        behavior_apply_detail, result = self._apply_behavior(chosen_behavior, 0.5) # 这里成功率先设定为0.5

        return ({
                    "behavior_name": chosen_behavior,          # 行为名，比如 "社交-朋友聚会"
                    "behavior_detail": behavior_apply_detail,  # 原始的最终文本，比如 "社交-朋友聚会【唱K】"
                    "behavior_result": result,                 # 进展顺利
                    "score": scores[chosen_behavior]           # 分数
                }, scores)

    def get_adjusted_state(self):
        return self.bps_state_vector

    def print_state(self):
        print("🔋 体力值: " + str(self.bio_energy))
        print("🔋 情绪效价:" + self.emotion_module.current_mood_valence())
        print("🔋 情绪唤醒:" + self.emotion_module.current_mood_arousal())
        dim_names = [
            "生理健康需求", "疼痛规避需求", "健康保护需求", "情绪反应需求",
            "风险规避需求", "目标坚持需求", "好奇探索需求", "规范遵循需求",
            "亲社会性需求", "社会形象需求", "角色责任需求", "群体归属需求"
        ]
        
        if len(self.bps_state_vector) != len(dim_names):
            print(f"⚠️ 状态向量维度数（{len(self.bps_state_vector)}）与名称数量不匹配（{len(dim_names)}）")
            return
        #print("\n".join(f"{name}: {round(val, 3)}" for name, val in zip(dim_names, self.bps_state_vector)))


# 每个行为的定义格式：基于Biopsychosocial的需求描述
#   "行为类型": {
#       "tag": string → 行为的类别 
#       "choice_bias": float → 行为被选中的倾向值（>1 更容易被选中，<1 更难被选中）
#       "bio_require": float → 行为要求的基本体力值（范围0~1:0代表没有基本体力要求，1代表要求体力充沛）
#       "bio_cunsumption": float → 行为执行后带来的体力值消耗（范围-1～1:-1代表对体力值减少，0代表对体力值无增无减，1代表体力值被恢复）
#       "psycho_cunsumption": float → 行为执行后带来的心理值消耗（范围-1～1:-1代表对心理值减少，0代表对心理值无增无减，1代表心理值被恢复）
#       "Weight": List[float] → 虚拟人的需求匹配，用于与虚拟人的12维状态进行点乘计算（下列为12维状态中每个参数的解释）
            #"biological_physiological_drive"      // 生理-本能需求：身体本能
            #"biological_pain_avoidance"           // 生理-伤害规避：规避风险、规避伤害
            #"biological_health_preservation"      // 生理-健康保护：保全身体、避免消耗
            #"psychological_emotional_reactivity"  // 心理-情绪激发：外部事件引发高情绪波动
            #"psychological_risk_aversion"         // 心理-风险规避：避免冲突、不确定或危险情境
            #"psychological_goal_persistence"      // 心理-目标坚持：坚持长远目标、抵抗诱惑
            #"psychological_curiosity_drive"       // 心理-探索好奇：新事物与未知经验的倾向
            #"social_norm_adherence"               // 社会-规范遵循：守规矩、按制度行事的程度
            #"social_prosocial_motivation"         // 社会-利他倾向：利他主义、帮助他人的倾向
            #"social_self_presentation"            // 社会-面子维护：在他人面前关注个体形象与体面
            #"social_role_duty_sense"              // 社会-角色责任：根据角色身份（如老师、父母）做出义务行为
            #"social_group_affiliation"            // 社会-群体归属：对团体的忠诚、集体目标的优先级
#       "Time": List[string] → "morning", "afternoon", "evening"
#       "Detail": List[string]
#   }

#基于Biopsychosocial的需求
#一个爱学习，低社交需求的人
personality1 = np.array([
    0.5,  # biological_physiological_drive     生理能量中等
    0.4,  # biological_pain_avoidance          伤害规避偏低
    0.6,  # biological_health_preservation     健康保护中等偏高
    0.5,  # psychological_emotional_reactivity 情绪激发性中等
    0.4,  # psychological_risk_aversion        风险规避偏低
    1.5,  # psychological_goal_persistence     目标坚持度高
    1.1,  # psychological_curiosity_drive      探索动机中等偏高
    0.2,  # social_norm_adherence              社会规范遵循低
    0.1,  # social_prosocial_motivation        亲社会动机低
    0.1,  # social_self_presentation           自我呈现/面子需求很低
    0.1,  # social_role_duty_sense             社会角色责任感低
    0.1   # social_group_affiliation           群体归属感低
])

#基于Biopsychosocial的需求
#一个高社交需求、善解人意的人
personality2 = np.array([
    0.6,  # biological_physiological_drive     生理能量中等偏高
    0.5,  # biological_pain_avoidance          伤害规避中等
    0.6,  # biological_health_preservation     健康保护中等
    0.7,  # psychological_emotional_reactivity 情绪激发性较高
    0.6,  # psychological_risk_aversion        风险规避中等偏高
    0.7,  # psychological_goal_persistence     目标坚持度较高
    0.5,  # psychological_curiosity_drive      探索动机中等
    0.7,  # social_norm_adherence              社会规范遵循高
    1.5,  # social_prosocial_motivation        亲社会动机非常高 ← 善解人意关键
    1.4,  # social_self_presentation           社会面子需求高（愿意被认同）
    1.5,  # social_role_duty_sense             社会责任感非常高 ← 善解人意关键
    1.4   # social_group_affiliation           群体归属感高 ← 高社交需求关键
])

#基于Biopsychosocial的驱动
#一个爱学习的人，性格开朗，爱运动的人
personality3 = np.array([
    0.9,  # biological_physiological_drive     生理能量高 ← 爱运动
    0.3,  # biological_pain_avoidance          疼痛规避低 ← 运动接受度高
    0.6,  # biological_health_preservation     健康保护中等
    0.8,  # psychological_emotional_reactivity 情绪激发性高 ← 性格开朗
    0.3,  # psychological_risk_aversion        风险规避低 ← 运动型探索型
    1.2,  # psychological_goal_persistence     目标坚持度高 ← 爱学习
    1.2,  # psychological_curiosity_drive      探索动机高 ← 爱学习
    0.7,  # social_norm_adherence              社会规范遵循中等偏高 ← 学习型
    0.9,  # social_prosocial_motivation        亲社会动机高 ← 性格外向
    0.9,  # social_self_presentation           面子需求高 ← 活跃外向
    0.7,  # social_role_duty_sense             社会责任感中等偏高
    0.9   # social_group_affiliation           群体归属感高 ← 喜社交运动
])

#基于Biopsychosocial的驱动
#一个热爱冒险，不怕风险，且喜欢独行的人
personality4 = np.array([
    1.5,  # biological_physiological_drive     生理能量高 ← 喜欢高体能挑战
    0.2,  # biological_pain_avoidance          疼痛规避很低 ← 敢冒险
    0.4,  # biological_health_preservation     健康保护偏低 ← 接受身体消耗
    1.4,  # psychological_emotional_reactivity 情绪激发性较高 ← 对冒险有兴奋感
    0.1,  # psychological_risk_aversion        风险规避极低 ← 不怕危险
    0.6,  # psychological_goal_persistence     目标坚持中等偏高 ← 能完成挑战
    1.5,  # psychological_curiosity_drive      探索动机极高 ← 热爱未知
    0.3,  # social_norm_adherence              社会规范遵循偏低 ← 较叛逆
    0.1,  # social_prosocial_motivation        亲社会动机低 ← 喜欢独行
    0.2,  # social_self_presentation           面子需求中等 ← 不太在意他人看法
    0.1,  # social_role_duty_sense             社会责任感低 ← 不受角色束缚
    0.1   # social_group_affiliation           群体归属感极低 ← 独行者
])

#基于Biopsychosocial的驱动
#一个爱玩不爱学习的人
personality5 = np.array([
    1.0,  # biological_physiological_drive     → 很爱动，偏好体感与刺激
    0.4,  # biological_pain_avoidance          → 不太怕辛苦，但不做痛苦事
    0.3,  # biological_health_preservation     → 健康意识低，易沉迷玩乐
    0.9,  # psychological_emotional_reactivity → 玩乐情绪反应强烈
    0.2,  # psychological_risk_aversion        → 风险意识很低，容易做冲动决策
    0.1,  # psychological_goal_persistence     → 极低的目标坚持度，无法坚持学习任务
    0.9,  # psychological_curiosity_drive      → 好奇心高但不深入（偏向浅层体验）
    0.3,  # social_norm_adherence              → 抗拒规矩、不守课堂纪律
    0.2,  # social_prosocial_motivation        → 不愿配合学习活动或集体目标
    0.6,  # social_self_presentation           → 在乎别人怎么看自己“酷不酷”
    0.2,  # social_role_duty_sense             → 学生角色责任感低
    0.4   # social_group_affiliation           → 不强烈归属感，可能逃避集体学习情境
])

#乐观派
emotional1 = np.array([
    0.0, # 当前的情绪效价（范围 -1.0 ~ 1.0），
    0.1, # 情绪效价的个体基准线（个性倾向），可用于表示一个人天生偏悲观或乐观（例如 -0.2 表示略偏负面）（范围 -1.0 ~ 1.0），
    0.5, # 情绪恢复速度（范围 0.0 ~ 1.0），
    0.5 # 个体对事件刺激的情绪反应强度（放大倍数），值越大 → 对行为结果更敏感，情绪波动更剧烈（范围 0.0 ~ 1.0），
])

#悲观派
emotional2 = np.array([
    0.0, # 当前的情绪效价（范围 -1.0 ~ 1.0），
    -0.2, # 情绪效价的个体基准线（个性倾向），可用于表示一个人天生偏悲观或乐观（例如 -0.2 表示略偏负面）（范围 -1.0 ~ 1.0），
    0.5, # 情绪恢复速度（范围 0.0 ~ 1.0），
    0.5 # 个体对事件刺激的情绪反应强度（放大倍数），值越大 → 对行为结果更敏感，情绪波动更剧烈（范围 0.0 ~ 1.0），
])