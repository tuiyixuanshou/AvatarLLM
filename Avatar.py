import numpy as np
import random

import numpy as np

class EmotionState:
    def __init__(self, personality_vector, emotional_vector):
        self.valence = emotional_vector[0]  # 当前的情绪效价（范围 -1.0 ~ 1.0), -1 表示极端负面情绪（如沮丧、愤怒）+1 表示极端正面情绪（如愉悦、兴奋）

        self.arousal = 0.5 # 情绪唤醒值，（范围 0.0 ~ 1.0)

        self.valence_baseline = emotional_vector[1]  # 情绪效价的个体基准线（个性倾向），可用于表示一个人天生偏悲观或乐观（例如 -0.2 表示略偏负面）

        self.valence_decay_rate = emotional_vector[2]  # 情绪回归中性状态的衰减速率，每一次 decay 调用时，valence 会以此比例向 baseline 回落
        
        self.valence_sensitivity = emotional_vector[3]  # 个体对事件刺激的情绪反应强度（放大倍数），值越大 → 对行为结果更敏感，情绪波动更剧烈

        self.personality = personality_vector

        # 从人格中提取目标坚持度，用于调节：行为成败是否强烈影响情绪
        self.goal_sensitivity = personality_vector[5] # psychological_goal_persistence

        # 从人格中提取情绪反应性，用于调节：情绪对刺激的放大程度（包括正面与负面）
        self.emotional_reactivity = personality_vector[3] # psychological_emotional_reactivity

        # 从人格中提取风险规避度，反向计算失败容忍度
        # 越害怕风险，越不能接受失败（所以 1 - 风险规避 = 容忍失败的能力）
        self.failure_tolerance = 1 - personality_vector[4] # psychological_risk_aversion

        # 从人格中提取“社会评价敏感度”，用于调节行为是否涉及形象/面子时的情绪影响
        self.social_feedback_sensitivity = personality_vector[9] # social_self_presentation

        # 从人格中提取探索好奇驱动，用于调节失败后的恢复力
        # 高探索欲的人面对失败容易重建积极情绪，看到失败为“经验”
        self.exploratory_resilience = personality_vector[6] # psychological_curiosity_drive
        
        self.frustration_level = 0.0 # 挫折状态
        self.mood_history = []

    def _estimate_valence_delta(self, behavior, psycho_cunsumption, success_value):
        # 融合估算：行为与人格的匹配 + 成败影响
        weight = np.array(behavior["Weight"])

        # 匹配得分：划分索引
        DIRECT_IDX = [3, 4, 5, 9, 10]
        INDIRECT_IDX = [6, 8, 11]

        direct_match = np.dot(weight[DIRECT_IDX], self.personality[DIRECT_IDX])
        indirect_match = np.dot(weight[INDIRECT_IDX], self.personality[INDIRECT_IDX])

        if success_value > 0.0:
            valence = (
                psycho_cunsumption +
                direct_match * 0.05 +
                indirect_match * 0.02
            )
        else:
            valence = (
                psycho_cunsumption -
                direct_match * 0.07 -
                indirect_match * 0.02
            )

        return valence

    def process_behavior(self, bio_energy, behavior, psycho_cunsumption, success_value):
        # 估算行为的valence影响，并更新当前状态
        valence_delta = self._estimate_valence_delta(behavior, psycho_cunsumption, success_value)
        modulator = self.valence_sensitivity * self.emotional_reactivity * 4.0

        if success_value < 0.0:
            tolerance = np.clip(self.failure_tolerance + self.exploratory_resilience * 0.5, 0.0, 1.0)
            modulator *= (1.0 - tolerance*0.2)
    
        adjustment = valence_delta * modulator
        self.valence += adjustment
        self.valence = np.clip(self.valence,-1.0,1.0)
        self.arousal = np.clip(0.6 * bio_energy + self.emotional_reactivity * self.valence_sensitivity * 0.2, 0.0, 1.0)

        if self.valence < -0.3:
            self.frustration_level += abs(self.valence) * 0.1
        else:
            self.frustration_level *= 0.9

        self.mood_history.append(self.valence)
        if len(self.mood_history)>5:
            self.mood_history.pop(0)

        #print("psycho_cunsumption:" + str(psycho_cunsumption))
        #print("valence_delta:" + str(valence_delta))
        #print("adjustment:" + str(adjustment))
        return 0

    def decay(self):
        self.valence = np.clip(self.valence * (1.0-self.valence_decay_rate) - self.valence_baseline * self.valence_decay_rate,-1.0,1.0)

    def current_mood_valence(self):
        v = self.valence
        if v > 0.6:
            return f"喜悦({v:.2f})"       # 高效价：明显幸福与兴奋
        elif v > 0.4:
            return f"满足({v:.2f})"       # 稍低于喜悦，更沉稳的正面情绪
        elif v > 0.2:
            return f"轻松({v:.2f})"       # 心情良好但非强烈积极
        elif v > -0.1:
            return f"平和({v:.2f})"       # 略偏正，安静平稳
        elif v > -0.2:
            return f"低落({v:.2f})"       # 稍微偏负，尚能调节
        elif v > -0.4:
            return f"消沉({v:.2f})"       # 显著负面，但未失控
        elif v > -0.6:
            return f"烦闷({v:.2f})"       # 情绪压抑，易爆发或内耗
        else:
            return f"沮丧({v:.2f})"       # 极度负面，接近抑郁或崩溃
        
    def current_mood_arousal(self):
        v = self.arousal
        if v > 0.8:
            return f"很强({v:.2f})"       # 极度激活状态，可能是兴奋、紧张、狂喜、焦躁
        elif v > 0.6:
            return f"较强({v:.2f})"       # 精神集中、充满动力，准备行动
        elif v > 0.4:
            return f"正常({v:.2f})"       # 中等唤醒，心情平衡、淡定从容
        elif v > 0.2:
            return f"较弱({v:.2f})"       # 有些困倦，精力低但未完全失控
        else:
            return f"很弱({v:.2f})"       # 极低激活，身心俱疲、难以应对

class VirtualAgent:
    def __init__(self, personality, emotional_vector, behavior_library):
        print("\n\n\n\n\n")
        print(f"\n🤖 Avatar创建--------------------------------------------")
        print("个性数值:" + str(personality))
        print("情绪数值:" + str(emotional_vector))

        self.personality = personality
        self.behavior_library = behavior_library
        self.bio_energy = 1.0 # 体力
        self.bps_state_vector = personality # BPS需求向量
        self.history = []
        self.behavior_fatigue = {}  # 记录每个行为的倦怠值 ∈ [0, 1]
        self.emotion = EmotionState(personality,emotional_vector) # 添加情绪系统

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
        self.emotion.process_behavior(self.bio_energy, behavior, psycho_cunsumption * dot_psycho_social_weight, success_value)


    def daily_update(self):
        # 生理值/心理值/情绪 每天恢复
        self.bio_energy = np.clip(self.bio_energy * 0.8 + 0.2, 0.0, 2.0)
        self.emotion.valence = np.clip(self.emotion.valence * 0.2 + self.emotion.valence_baseline * 0.8, -1, 1.0)
        self.emotion.arousal = np.clip(self.emotion.arousal * 0.2 + 0.5 * 0.8, 0.0, 1.0)

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
        self.emotion.decay()
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
            emotion_modifier = 1.0 + 0.25 * self.emotion.valence + 0.25 * (self.emotion.arousal - 0.5)
            emotion_modifier = np.clip(emotion_modifier, 0.75, 1.25)

            # ==== 抗拒因子（含情绪）====
            physical_resistance = pow(np.clip(self.bio_energy + bio_motivation * 0.5, 0.0, 1.0), 0.5) * emotion_modifier
            mental_resistance = pow(np.clip((self.emotion.valence*0.5+0.5) + psycho_motivation * 0.5, 0.0, 1.0), 0.5) * emotion_modifier

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

    def _apply_behavior(self, chosen_behavior, success_rate=0.7):
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

        # 随机选择 Detail 描述（如有）
        behavior_data = self.behavior_library.get(chosen_behavior, {})
        details = behavior_data.get("Detail", [])
        selected_detail = random.choice(details) if details else None

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
            return chosen_behavior + "【" + selected_detail + "】"
        else:
            return chosen_behavior + "【" + selected_detail + "(" + success + ")】"

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

        info = self._apply_behavior(chosen_behavior, 0.5) # 这里成功率先设定为0.5

        return (info, scores[chosen_behavior]), scores

    def get_adjusted_state(self):
        return self.bps_state_vector

    def _log(self, source, delta):
        self.history.append({
            'source': source,
            'state': self.bps_state_vector.copy(),
            'delta': delta.copy()
        })

    def print_state(self):
        print("🔋 体力值: " + str(self.bio_energy))
        print("🔋 情绪效价:" + self.emotion.current_mood_valence())
        print("🔋 情绪唤醒:" + self.emotion.current_mood_arousal())
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
# import json

# with open("M_file\\Event_pool.json", "r", encoding="utf-8") as f:
#     behavior_library = json.load(f)
# agent = VirtualAgent(personality5, emotional1, behavior_library)

# # 模拟 7 天：早中晚各一行为
# for day in range(30):
#     print(f"\n📅 Day {day}-------------------------------------------------")
#     agent.print_state()
#     for Time_slot in ["morning", "afternoon", "evening"]:
#         result = agent.select_best_behavior(top_k=2, current_Time_slot=Time_slot)
#         if result[0]:
#             best_behavior, score = result[0]
#             print(f"🕒 {Time_slot.upper()}: {best_behavior}")
#         else:
#             print("⚠️ 当前时段无可选行为")
#         agent.print_state()
#     print()
#     agent.daily_update()