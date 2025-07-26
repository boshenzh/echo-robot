import time
import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict
import math

class BreakType(Enum):
    """休息类型枚举"""
    MICRO_BREAK = "micro_break"      # 微休息 (1-2分钟)
    SHORT_BREAK = "short_break"      # 短休息 (5-10分钟)
    LONG_BREAK = "long_break"        # 长休息 (15-30分钟)
    POWER_NAP = "power_nap"          # 小憩 (20-30分钟)
    EXERCISE_BREAK = "exercise_break" # 运动休息 (10-15分钟)

@dataclass
class BreakRecommendation:
    """休息建议数据结构"""
    break_type: BreakType
    recommended_duration: int  # 分钟
    urgency_level: int        # 1-5级紧急程度
    reason: str              # 建议原因
    suggested_activities: List[str]  # 建议活动
    confidence_score: float   # 0-1置信度
    optimal_timing: bool     # 是否为最佳时机

class IntelligentBreakAdvisor:
    """智能休息建议系统"""
    
    def __init__(self):
        self.attention_history = []
        self.stress_history = []
        self.focus_score_history = []
        self.last_break_time = 0
        self.session_start_time = time.time()
        
        # 分析参数
        self.low_attention_threshold = 0.4
        self.high_stress_threshold = 0.7
        self.fatigue_duration_threshold = 1800  # 30分钟
        self.min_break_interval = 300  # 5分钟最小间隔
        
        # 活动建议库
        self.activity_suggestions = {
            BreakType.MICRO_BREAK: [
                "深呼吸3次",
                "眨眼20次缓解眼疲劳", 
                "伸展颈部和肩膀",
                "喝一口水",
                "看向远处放松眼睛"
            ],
            BreakType.SHORT_BREAK: [
                "起身走动5分钟",
                "做简单的伸展运动",
                "洗把脸清醒一下",
                "听一首轻松的音乐",
                "做眼保健操",
                "整理桌面环境"
            ],
            BreakType.LONG_BREAK: [
                "出门散步15-20分钟",
                "做瑜伽或冥想",
                "吃点健康零食",
                "与朋友聊天放松",
                "听播客或音乐",
                "做家务活动身体"
            ],
            BreakType.POWER_NAP: [
                "找安静地方小憩20分钟",
                "播放白噪音助眠",
                "使用眼罩和耳塞",
                "设置闹钟避免睡过头"
            ],
            BreakType.EXERCISE_BREAK: [
                "做10个俯卧撑",
                "原地跑步2分钟", 
                "做拉伸运动",
                "爬楼梯几层",
                "做简单的力量训练"
            ]
        }
    
    def analyze_and_recommend(self, attention: float, stress: float, 
                            focus_score: float, session_duration: float) -> Optional[BreakRecommendation]:
        """分析当前状态并生成休息建议"""
        
        # 更新历史数据
        current_time = time.time()
        self.attention_history.append((current_time, attention))
        self.stress_history.append((current_time, stress))
        self.focus_score_history.append((current_time, focus_score))
        
        # 清理过期数据（保留最近30分钟）
        cutoff_time = current_time - 1800
        self.attention_history = [(t, v) for t, v in self.attention_history if t > cutoff_time]
        self.stress_history = [(t, v) for t, v in self.stress_history if t > cutoff_time]
        self.focus_score_history = [(t, v) for t, v in self.focus_score_history if t > cutoff_time]
        
        # 检查是否需要休息建议
        if current_time - self.last_break_time < self.min_break_interval:
            return None
        
        # 分析各种休息触发条件
        recommendations = []
        
        # 1. 基于专注度的分析
        if attention < self.low_attention_threshold:
            urgency = self._calculate_urgency(attention, 0.4, inverse=True)
            recommendations.append(self._create_attention_break(attention, urgency))
        
        # 2. 基于压力的分析  
        if stress > self.high_stress_threshold:
            urgency = self._calculate_urgency(stress, 0.7)
            recommendations.append(self._create_stress_break(stress, urgency))
        
        # 3. 基于疲劳的分析
        if session_duration > self.fatigue_duration_threshold:
            urgency = self._calculate_fatigue_urgency(session_duration)
            recommendations.append(self._create_fatigue_break(session_duration, urgency))
        
        # 4. 基于趋势的分析
        trend_recommendation = self._analyze_trends()
        if trend_recommendation:
            recommendations.append(trend_recommendation)
        
        # 5. 基于生物节律的分析（可选）
        circadian_recommendation = self._analyze_circadian_rhythm()
        if circadian_recommendation:
            recommendations.append(circadian_recommendation)
        
        # 选择最佳建议
        if recommendations:
            best_recommendation = max(recommendations, key=lambda x: x.urgency_level * x.confidence_score)
            self.last_break_time = current_time
            return best_recommendation
        
        return None
    
    def _calculate_urgency(self, value: float, threshold: float, inverse: bool = False) -> int:
        """计算紧急程度 (1-5)"""
        if inverse:
            # 值越低越紧急（如注意力）
            ratio = (threshold - value) / threshold
        else:
            # 值越高越紧急（如压力）
            ratio = (value - threshold) / (1 - threshold)
        
        ratio = max(0, min(1, ratio))
        return int(ratio * 4) + 1
    
    def _create_attention_break(self, attention: float, urgency: int) -> BreakRecommendation:
        """创建基于注意力的休息建议"""
        if attention < 0.2:
            break_type = BreakType.LONG_BREAK
            duration = 15
            reason = "注意力严重不足，需要长时间休息恢复"
        elif attention < 0.3:
            break_type = BreakType.SHORT_BREAK
            duration = 8
            reason = "注意力较低，建议短暂休息调整"
        else:
            break_type = BreakType.MICRO_BREAK
            duration = 2
            reason = "注意力略有下降，微休息即可"
        
        activities = random.sample(self.activity_suggestions[break_type], 
                                 min(3, len(self.activity_suggestions[break_type])))
        
        return BreakRecommendation(
            break_type=break_type,
            recommended_duration=duration,
            urgency_level=urgency,
            reason=reason,
            suggested_activities=activities,
            confidence_score=0.8,
            optimal_timing=True
        )
    
    def _create_stress_break(self, stress: float, urgency: int) -> BreakRecommendation:
        """创建基于压力的休息建议"""
        if stress > 0.9:
            break_type = BreakType.POWER_NAP
            duration = 20
            reason = "压力过高，建议小憩放松身心"
        elif stress > 0.8:
            break_type = BreakType.LONG_BREAK
            duration = 15
            reason = "压力较高，需要较长时间缓解"
        else:
            break_type = BreakType.SHORT_BREAK
            duration = 5
            reason = "压力上升，建议适当放松"
        
        activities = random.sample(self.activity_suggestions[break_type], 
                                 min(3, len(self.activity_suggestions[break_type])))
        
        return BreakRecommendation(
            break_type=break_type,
            recommended_duration=duration,
            urgency_level=urgency,
            reason=reason,
            suggested_activities=activities,
            confidence_score=0.85,
            optimal_timing=True
        )
    
    def _create_fatigue_break(self, duration: float, urgency: int) -> BreakRecommendation:
        """创建基于疲劳的休息建议"""
        hours = duration / 3600
        
        if hours > 2:
            break_type = BreakType.POWER_NAP
            break_duration = 25
            reason = f"连续专注{hours:.1f}小时，身心疲劳需要小憩"
        elif hours > 1.5:
            break_type = BreakType.EXERCISE_BREAK
            break_duration = 12
            reason = f"连续专注{hours:.1f}小时，建议运动激活身体"
        else:
            break_type = BreakType.LONG_BREAK
            break_duration = 15
            reason = f"连续专注{hours:.1f}小时，需要较长时间恢复"
        
        activities = random.sample(self.activity_suggestions[break_type], 
                                 min(3, len(self.activity_suggestions[break_type])))
        
        return BreakRecommendation(
            break_type=break_type,
            recommended_duration=break_duration,
            urgency_level=urgency,
            reason=reason,
            suggested_activities=activities,
            confidence_score=0.9,
            optimal_timing=True
        )
    
    def _calculate_fatigue_urgency(self, duration: float) -> int:
        """计算疲劳紧急程度"""
        hours = duration / 3600
        if hours > 3:
            return 5
        elif hours > 2:
            return 4
        elif hours > 1.5:
            return 3
        elif hours > 1:
            return 2
        else:
            return 1
    
    def _analyze_trends(self) -> Optional[BreakRecommendation]:
        """分析趋势变化"""
        if len(self.attention_history) < 10 or len(self.stress_history) < 10:
            return None
        
        # 分析最近10个数据点的趋势
        recent_attention = [v for _, v in self.attention_history[-10:]]
        recent_stress = [v for _, v in self.stress_history[-10:]]
        
        # 计算趋势斜率
        attention_trend = self._calculate_trend_slope(recent_attention)
        stress_trend = self._calculate_trend_slope(recent_stress)
        
        # 注意力下降且压力上升的危险趋势
        if attention_trend < -0.02 and stress_trend > 0.02:
            return BreakRecommendation(
                break_type=BreakType.SHORT_BREAK,
                recommended_duration=8,
                urgency_level=4,
                reason="检测到注意力下降且压力上升的不良趋势",
                suggested_activities=random.sample(self.activity_suggestions[BreakType.SHORT_BREAK], 3),
                confidence_score=0.75,
                optimal_timing=True
            )
        
        return None
    
    def _calculate_trend_slope(self, values: List[float]) -> float:
        """计算趋势斜率"""
        if len(values) < 2:
            return 0
        
        n = len(values)
        x = list(range(n))
        y = values
        
        # 简单线性回归计算斜率
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        return slope
    
    def _analyze_circadian_rhythm(self) -> Optional[BreakRecommendation]:
        """基于生物节律的分析（简化版）"""
        current_hour = time.localtime().tm_hour
        
        # 下午疲劳期 (14:00-16:00)
        if 14 <= current_hour <= 16:
            if random.random() < 0.3:  # 30%概率建议
                return BreakRecommendation(
                    break_type=BreakType.POWER_NAP,
                    recommended_duration=20,
                    urgency_level=2,
                    reason="下午疲劳期，适合小憩恢复精力",
                    suggested_activities=self.activity_suggestions[BreakType.POWER_NAP],
                    confidence_score=0.6,
                    optimal_timing=True
                )
        
        return None
    
    def reset_session(self):
        """重置会话数据"""
        self.attention_history.clear()
        self.stress_history.clear()
        self.focus_score_history.clear()
        self.last_break_time = 0
        self.session_start_time = time.time()
    
    def get_break_statistics(self) -> Dict:
        """获取休息统计信息"""
        current_time = time.time()
        session_duration = current_time - self.session_start_time
        
        # 计算平均值
        avg_attention = sum(v for _, v in self.attention_history) / len(self.attention_history) if self.attention_history else 0
        avg_stress = sum(v for _, v in self.stress_history) / len(self.stress_history) if self.stress_history else 0
        avg_focus = sum(v for _, v in self.focus_score_history) / len(self.focus_score_history) if self.focus_score_history else 0
        
        return {
            'session_duration': session_duration,
            'average_attention': avg_attention,
            'average_stress': avg_stress,
            'average_focus_score': avg_focus,
            'time_since_last_break': current_time - self.last_break_time,
            'data_points_collected': len(self.attention_history)
        }

# 测试代码
if __name__ == "__main__":
    print("🧠 智能休息建议系统测试")
    
    advisor = IntelligentBreakAdvisor()
    
    # 模拟不同状态的测试
    test_cases = [
        (0.3, 0.8, 0.4, 1800),   # 低注意力，高压力，30分钟
        (0.8, 0.3, 0.7, 900),    # 高注意力，低压力，15分钟  
        (0.2, 0.9, 0.2, 3600),   # 极低注意力，极高压力，1小时
        (0.6, 0.5, 0.6, 600),    # 正常状态，10分钟
    ]
    
    for i, (attention, stress, focus_score, duration) in enumerate(test_cases):
        print(f"\n📊 测试案例 {i+1}:")
        print(f"   注意力: {attention:.1f}, 压力: {stress:.1f}, 专注评分: {focus_score:.1f}")
        print(f"   会话时长: {duration/60:.1f}分钟")
        
        recommendation = advisor.analyze_and_recommend(attention, stress, focus_score, duration)
        
        if recommendation:
            print(f"💡 休息建议:")
            print(f"   类型: {recommendation.break_type.value}")
            print(f"   时长: {recommendation.recommended_duration}分钟")
            print(f"   紧急程度: {recommendation.urgency_level}/5")
            print(f"   原因: {recommendation.reason}")
            print(f"   建议活动: {', '.join(recommendation.suggested_activities)}")
            print(f"   置信度: {recommendation.confidence_score:.2f}")
        else:
            print("💡 暂无休息建议")
        
        # 模拟时间间隔
        advisor.last_break_time -= 400  # 减少冷却时间以便测试
    
    print("\n📈 统计信息:")
    stats = advisor.get_break_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")
    
    print("✅ 测试完成")