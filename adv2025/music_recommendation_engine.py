import time
import random
import json
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import math

class MusicType(Enum):
    """音乐类型枚举"""
    FOCUS_AMBIENT = "focus_ambient"      # 专注环境音
    CLASSICAL = "classical"              # 古典音乐
    NATURE_SOUNDS = "nature_sounds"      # 自然声音
    WHITE_NOISE = "white_noise"          # 白噪音
    BINAURAL_BEATS = "binaural_beats"    # 双耳节拍
    RELAXATION = "relaxation"            # 放松音乐
    INSTRUMENTAL = "instrumental"        # 器乐音乐
    MEDITATION = "meditation"            # 冥想音乐

@dataclass
class MusicTrack:
    """音乐曲目数据结构"""
    title: str
    artist: str
    duration: str  # MM:SS格式
    music_type: MusicType
    bpm: int  # 每分钟节拍数
    energy_level: float  # 0-1能量水平
    focus_effectiveness: float  # 0-1专注有效性

@dataclass
class MusicRecommendation:
    """音乐推荐数据结构"""
    tracks: List[MusicTrack]
    reason: str
    adaptive_volume: float  # 0-1推荐音量
    duration_minutes: int
    confidence_score: float  # 0-1置信度
    music_type: MusicType

class MusicRecommendationEngine:
    """智能音乐推荐引擎"""
    
    def __init__(self):
        self.user_preferences = self._load_user_preferences()
        self.music_library = self._initialize_music_library()
        self.listening_history = []
        self.current_session_data = []
        
        # 推荐参数
        self.attention_threshold_high = 0.7
        self.attention_threshold_low = 0.4
        self.stress_threshold_high = 0.7
        self.stress_threshold_low = 0.3
        
    def _load_user_preferences(self) -> Dict:
        """加载用户偏好设置"""
        default_preferences = {
            'preferred_types': [MusicType.FOCUS_AMBIENT, MusicType.CLASSICAL],
            'disliked_types': [],
            'volume_preference': 0.5,
            'session_length_preference': 30,  # 分钟
            'adaptive_volume': True,
            'prefer_instrumental': True
        }
        
        try:
            with open('config/music_preferences.json', 'r') as f:
                preferences = json.load(f)
                # 转换枚举类型
                if 'preferred_types' in preferences:
                    preferences['preferred_types'] = [MusicType(t) for t in preferences['preferred_types']]
                if 'disliked_types' in preferences:
                    preferences['disliked_types'] = [MusicType(t) for t in preferences['disliked_types']]
                default_preferences.update(preferences)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        return default_preferences
    
    def _initialize_music_library(self) -> Dict[MusicType, List[MusicTrack]]:
        """初始化音乐库"""
        library = {
            MusicType.FOCUS_AMBIENT: [
                MusicTrack("深度专注", "环境音大师", "45:00", MusicType.FOCUS_AMBIENT, 60, 0.3, 0.9),
                MusicTrack("雨声工作室", "自然之声", "60:00", MusicType.FOCUS_AMBIENT, 0, 0.2, 0.8),
                MusicTrack("咖啡厅氛围", "城市声景", "30:00", MusicType.FOCUS_AMBIENT, 65, 0.4, 0.7),
            ],
            MusicType.CLASSICAL: [
                MusicTrack("巴赫变奏曲", "古典精选", "25:00", MusicType.CLASSICAL, 120, 0.5, 0.8),
                MusicTrack("莫扎特奏鸣曲", "维也纳爱乐", "35:00", MusicType.CLASSICAL, 110, 0.4, 0.9),
                MusicTrack("德彪西月光", "钢琴大师", "15:00", MusicType.CLASSICAL, 80, 0.3, 0.7),
            ],
            MusicType.NATURE_SOUNDS: [
                MusicTrack("森林晨曲", "大自然录音", "60:00", MusicType.NATURE_SOUNDS, 0, 0.2, 0.6),
                MusicTrack("海浪声", "海洋之音", "45:00", MusicType.NATURE_SOUNDS, 0, 0.3, 0.7),
                MusicTrack("鸟鸣山谷", "野生录音", "40:00", MusicType.NATURE_SOUNDS, 0, 0.4, 0.5),
            ],
            MusicType.WHITE_NOISE: [
                MusicTrack("纯白噪音", "声音疗法", "120:00", MusicType.WHITE_NOISE, 0, 0.1, 0.8),
                MusicTrack("粉红噪音", "睡眠助手", "90:00", MusicType.WHITE_NOISE, 0, 0.1, 0.7),
                MusicTrack("棕色噪音", "专注工具", "60:00", MusicType.WHITE_NOISE, 0, 0.1, 0.9),
            ],
            MusicType.BINAURAL_BEATS: [
                MusicTrack("Alpha波 10Hz", "脑波调节", "30:00", MusicType.BINAURAL_BEATS, 0, 0.3, 0.9),
                MusicTrack("Beta波 15Hz", "专注增强", "45:00", MusicType.BINAURAL_BEATS, 0, 0.5, 0.8),
                MusicTrack("Theta波 6Hz", "创意激发", "25:00", MusicType.BINAURAL_BEATS, 0, 0.2, 0.6),
            ],
            MusicType.RELAXATION: [
                MusicTrack("深度放松", "冥想音乐", "40:00", MusicType.RELAXATION, 60, 0.2, 0.3),
                MusicTrack("禅境", "东方禅音", "35:00", MusicType.RELAXATION, 50, 0.1, 0.4),
                MusicTrack("舒缓流水", "自然疗愈", "50:00", MusicType.RELAXATION, 55, 0.2, 0.5),
            ],
            MusicType.INSTRUMENTAL: [
                MusicTrack("钢琴独奏", "现代器乐", "28:00", MusicType.INSTRUMENTAL, 100, 0.4, 0.7),
                MusicTrack("吉他指弹", "民谣精选", "32:00", MusicType.INSTRUMENTAL, 90, 0.5, 0.6),
                MusicTrack("小提琴协奏", "室内乐团", "22:00", MusicType.INSTRUMENTAL, 120, 0.6, 0.8),
            ],
            MusicType.MEDITATION: [
                MusicTrack("正念冥想", "内观音乐", "30:00", MusicType.MEDITATION, 45, 0.1, 0.2),
                MusicTrack("西藏颂钵", "藏传音乐", "40:00", MusicType.MEDITATION, 40, 0.1, 0.3),
                MusicTrack("水晶音疗", "能量音乐", "35:00", MusicType.MEDITATION, 50, 0.2, 0.4),
            ]
        }
        
        return library
    
    def recommend_music(self, attention: float, stress: float, 
                       focus_score: float, session_duration: float) -> Optional[MusicRecommendation]:
        """基于当前状态推荐音乐"""
        
        # 更新会话数据
        self.current_session_data.append({
            'timestamp': time.time(),
            'attention': attention,
            'stress': stress,
            'focus_score': focus_score,
            'session_duration': session_duration
        })
        
        # 分析当前状态并选择音乐类型
        recommended_type = self._analyze_state_for_music_type(attention, stress, focus_score)
        
        # 获取该类型的音乐
        available_tracks = self.music_library.get(recommended_type, [])
        if not available_tracks:
            recommended_type = MusicType.FOCUS_AMBIENT  # 默认类型
            available_tracks = self.music_library[recommended_type]
        
        # 根据用户偏好和当前状态筛选
        filtered_tracks = self._filter_tracks_by_preferences(available_tracks, attention, stress)
        
        # 选择最适合的曲目
        selected_tracks = self._select_optimal_tracks(filtered_tracks, session_duration)
        
        # 计算推荐音量
        adaptive_volume = self._calculate_adaptive_volume(attention, stress)
        
        # 生成推荐原因
        reason = self._generate_recommendation_reason(attention, stress, focus_score, recommended_type)
        
        # 计算置信度
        confidence = self._calculate_recommendation_confidence(attention, stress, recommended_type)
        
        return MusicRecommendation(
            tracks=selected_tracks,
            reason=reason,
            adaptive_volume=adaptive_volume,
            duration_minutes=int(session_duration / 60) if session_duration > 0 else 30,
            confidence_score=confidence,
            music_type=recommended_type
        )
    
    def _analyze_state_for_music_type(self, attention: float, stress: float, focus_score: float) -> MusicType:
        """分析状态并选择最适合的音乐类型"""
        
        # 高压力状态 - 需要放松
        if stress > self.stress_threshold_high:
            if focus_score < 0.3:
                return MusicType.MEDITATION  # 极度疲劳需要冥想
            else:
                return MusicType.RELAXATION  # 一般高压力需要放松
        
        # 低注意力状态 - 需要激活
        elif attention < self.attention_threshold_low:
            if stress < self.stress_threshold_low:
                return MusicType.BINAURAL_BEATS  # 低压力低注意力用脑波
            else:
                return MusicType.WHITE_NOISE  # 有压力时用白噪音
        
        # 高注意力状态 - 维持专注
        elif attention > self.attention_threshold_high:
            if stress < self.stress_threshold_low:
                return MusicType.CLASSICAL  # 状态好时听古典
            else:
                return MusicType.INSTRUMENTAL  # 有点压力听器乐
        
        # 中等状态 - 通用选择
        else:
            return MusicType.FOCUS_AMBIENT  # 默认环境音
    
    def _filter_tracks_by_preferences(self, tracks: List[MusicTrack], 
                                    attention: float, stress: float) -> List[MusicTrack]:
        """根据用户偏好和当前状态过滤曲目"""
        filtered = []
        
        for track in tracks:
            # 检查用户偏好
            if track.music_type in self.user_preferences.get('disliked_types', []):
                continue
            
            # 根据注意力水平过滤
            if attention < 0.3 and track.energy_level > 0.7:  # 低注意力时避免高能量
                continue
            
            if attention > 0.8 and track.energy_level < 0.2:  # 高注意力时避免过低能量
                continue
            
            # 根据压力水平过滤
            if stress > 0.7 and track.energy_level > 0.5:  # 高压力时避免高能量
                continue
            
            filtered.append(track)
        
        return filtered if filtered else tracks  # 如果过滤后为空，返回原列表
    
    def _select_optimal_tracks(self, tracks: List[MusicTrack], session_duration: float) -> List[MusicTrack]:
        """选择最优曲目组合"""
        if not tracks:
            return []
        
        # 根据专注有效性排序
        sorted_tracks = sorted(tracks, key=lambda t: t.focus_effectiveness, reverse=True)
        
        # 选择前几首或根据时长需求选择
        target_duration_minutes = max(30, int(session_duration / 60)) if session_duration > 0 else 30
        
        selected = []
        total_duration = 0
        
        for track in sorted_tracks:
            # 解析时长
            duration_parts = track.duration.split(':')
            track_minutes = int(duration_parts[0])
            if len(duration_parts) > 1:
                track_minutes += int(duration_parts[1]) / 60
            
            if total_duration + track_minutes <= target_duration_minutes * 1.2:  # 允许20%的超出
                selected.append(track)
                total_duration += track_minutes
                
                if total_duration >= target_duration_minutes:
                    break
        
        return selected if selected else [sorted_tracks[0]]  # 至少返回一首
    
    def _calculate_adaptive_volume(self, attention: float, stress: float) -> float:
        """计算自适应音量"""
        base_volume = self.user_preferences.get('volume_preference', 0.5)
        
        if not self.user_preferences.get('adaptive_volume', True):
            return base_volume
        
        # 根据状态调整音量
        volume_adjustment = 0
        
        # 低注意力时稍微提高音量
        if attention < 0.4:
            volume_adjustment += 0.1
        
        # 高压力时降低音量
        if stress > 0.7:
            volume_adjustment -= 0.15
        
        # 极低注意力且高压力时大幅降低音量
        if attention < 0.3 and stress > 0.8:
            volume_adjustment -= 0.2
        
        adjusted_volume = base_volume + volume_adjustment
        return max(0.1, min(0.9, adjusted_volume))  # 限制在0.1-0.9范围
    
    def _generate_recommendation_reason(self, attention: float, stress: float, 
                                      focus_score: float, music_type: MusicType) -> str:
        """生成推荐原因说明"""
        reasons = []
        
        # 基于注意力的原因
        if attention < 0.3:
            reasons.append("注意力较低，需要激活大脑")
        elif attention > 0.8:
            reasons.append("注意力良好，适合维持专注状态")
        
        # 基于压力的原因
        if stress > 0.7:
            reasons.append("压力较高，建议放松缓解")
        elif stress < 0.3:
            reasons.append("压力较低，状态良好")
        
        # 基于音乐类型的原因
        type_reasons = {
            MusicType.FOCUS_AMBIENT: "环境音有助于保持专注而不分心",
            MusicType.CLASSICAL: "古典音乐能够提升认知表现",
            MusicType.NATURE_SOUNDS: "自然声音有助于放松和专注",
            MusicType.WHITE_NOISE: "白噪音能够屏蔽干扰提高专注",
            MusicType.BINAURAL_BEATS: "双耳节拍可以调节脑波状态",
            MusicType.RELAXATION: "放松音乐有助于缓解压力",
            MusicType.INSTRUMENTAL: "器乐音乐既不干扰又能提升情绪",
            MusicType.MEDITATION: "冥想音乐有助于深度放松和恢复"
        }
        
        reasons.append(type_reasons.get(music_type, "适合当前状态"))
        
        return "，".join(reasons)
    
    def _calculate_recommendation_confidence(self, attention: float, stress: float, 
                                          music_type: MusicType) -> float:
        """计算推荐置信度"""
        base_confidence = 0.7
        
        # 根据状态明确性调整置信度
        state_clarity = abs(attention - 0.5) + abs(stress - 0.5)  # 状态越极端越明确
        confidence_adjustment = state_clarity * 0.3
        
        # 根据音乐类型匹配度调整
        if music_type in self.user_preferences.get('preferred_types', []):
            confidence_adjustment += 0.2
        elif music_type in self.user_preferences.get('disliked_types', []):
            confidence_adjustment -= 0.3
        
        final_confidence = base_confidence + confidence_adjustment
        return max(0.1, min(0.95, final_confidence))
    
    def start_playlist(self) -> bool:
        """启动播放列表（模拟）"""
        print("🎵 开始播放音乐...")
        return True
    
    def stop_playlist(self) -> bool:
        """停止播放列表（模拟）"""
        print("⏹️ 停止播放音乐...")
        return True
    
    def update_user_feedback(self, liked: bool, music_type: MusicType):
        """更新用户反馈"""
        if liked:
            if music_type not in self.user_preferences['preferred_types']:
                self.user_preferences['preferred_types'].append(music_type)
            if music_type in self.user_preferences['disliked_types']:
                self.user_preferences['disliked_types'].remove(music_type)
        else:
            if music_type not in self.user_preferences['disliked_types']:
                self.user_preferences['disliked_types'].append(music_type)
            if music_type in self.user_preferences['preferred_types']:
                self.user_preferences['preferred_types'].remove(music_type)
        
        self._save_user_preferences()
    
    def _save_user_preferences(self):
        """保存用户偏好"""
        try:
            # 转换枚举为字符串以便JSON序列化
            saveable_prefs = self.user_preferences.copy()
            saveable_prefs['preferred_types'] = [t.value for t in saveable_prefs['preferred_types']]
            saveable_prefs['disliked_types'] = [t.value for t in saveable_prefs['disliked_types']]
            
            with open('config/music_preferences.json', 'w') as f:
                json.dump(saveable_prefs, f, indent=4)
        except Exception as e:
            print(f"保存用户偏好失败: {e}")
    
    def get_session_statistics(self) -> Dict:
        """获取会话统计信息"""
        if not self.current_session_data:
            return {}
        
        # 计算平均值
        avg_attention = sum(d['attention'] for d in self.current_session_data) / len(self.current_session_data)
        avg_stress = sum(d['stress'] for d in self.current_session_data) / len(self.current_session_data)
        avg_focus = sum(d['focus_score'] for d in self.current_session_data) / len(self.current_session_data)
        
        return {
            'total_recommendations': len(self.listening_history),
            'session_data_points': len(self.current_session_data),
            'average_attention': avg_attention,
            'average_stress': avg_stress,
            'average_focus_score': avg_focus,
            'preferred_music_types': [t.value for t in self.user_preferences['preferred_types']]
        }

# 测试代码
if __name__ == "__main__":
    print("🎵 智能音乐推荐引擎测试")
    
    engine = MusicRecommendationEngine()
    
    # 测试不同状态的音乐推荐
    test_scenarios = [
        (0.8, 0.2, 0.8, 1800, "高专注低压力"),
        (0.3, 0.8, 0.3, 2400, "低专注高压力"),
        (0.5, 0.5, 0.6, 1200, "平衡状态"),
        (0.2, 0.9, 0.2, 3600, "疲劳状态"),
        (0.9, 0.1, 0.9, 900, "最佳状态")
    ]
    
    for attention, stress, focus_score, duration, description in test_scenarios:
        print(f"\n📊 测试场景: {description}")
        print(f"   注意力: {attention:.1f}, 压力: {stress:.1f}, 专注评分: {focus_score:.1f}")
        print(f"   会话时长: {duration/60:.1f}分钟")
        
        recommendation = engine.recommend_music(attention, stress, focus_score, duration)
        
        if recommendation:
            print(f"🎵 音乐推荐:")
            print(f"   类型: {recommendation.music_type.value}")
            print(f"   原因: {recommendation.reason}")
            print(f"   推荐音量: {recommendation.adaptive_volume:.1f}")
            print(f"   时长: {recommendation.duration_minutes}分钟")
            print(f"   置信度: {recommendation.confidence_score:.2f}")
            print(f"   曲目数: {len(recommendation.tracks)}")
            for i, track in enumerate(recommendation.tracks[:2]):  # 显示前2首
                print(f"     {i+1}. {track.title} - {track.artist} ({track.duration})")
        else:
            print("🎵 暂无音乐推荐")
    
    print(f"\n📈 统计信息:")
    stats = engine.get_session_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.3f}")
        else:
            print(f"   {key}: {value}")
    
    print("✅ 测试完成")