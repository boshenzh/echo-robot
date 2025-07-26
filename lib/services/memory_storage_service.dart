import '../models/focus_session.dart';
import '../models/task.dart';

class MemoryStorageService {
  static final MemoryStorageService _instance = MemoryStorageService._internal();
  factory MemoryStorageService() => _instance;
  MemoryStorageService._internal();

  final List<Task> _activationTasks = [
    Task(
      id: 'act_1',
      title: '大声说出你看到的5样东西',
      description: '环顾四周，说出你能在环境中看到的5个物体',
      type: TaskType.activation,
    ),
    Task(
      id: 'act_2',
      title: '触摸周围的4种不同材质',
      description: '找到并触摸你周围环境中的4种不同材质',
      type: TaskType.activation,
    ),
    Task(
      id: 'act_3',
      title: '站起来伸展',
      description: '站起来做30秒的轻柔伸展',
      type: TaskType.activation,
    ),
    Task(
      id: 'act_4',
      title: '喝一杯水',
      description: '花点时间专注地喝完一整杯水',
      type: TaskType.activation,
    ),
    Task(
      id: 'act_5',
      title: '做3次深呼吸',
      description: '舒适地坐着，做3次缓慢的深呼吸',
      type: TaskType.activation,
    ),
  ];

  final List<Task> _breakTasks = [
    Task(
      id: 'break_1',
      title: '看窗外1分钟',
      description: '找到一扇窗户，观察外面的景色',
      type: TaskType.breakTask,
      durationMinutes: 1,
    ),
    Task(
      id: 'break_2',
      title: '给植物浇水',
      description: '照顾你空间里的一盆植物',
      type: TaskType.breakTask,
      durationMinutes: 2,
    ),
    Task(
      id: 'break_3',
      title: '喝茶',
      description: '专注地泡一杯茶并享受',
      type: TaskType.breakTask,
      durationMinutes: 5,
    ),
    Task(
      id: 'break_4',
      title: '轻柔的颈部伸展',
      description: '做一些轻柔的颈部和肩部伸展',
      type: TaskType.breakTask,
      durationMinutes: 3,
    ),
    Task(
      id: 'break_5',
      title: '短暂外出',
      description: '到外面待一会儿，感受空气',
      type: TaskType.breakTask,
      durationMinutes: 2,
    ),
  ];

  final List<FocusSession> _sessions = [];

  // Focus Session operations
  Future<void> insertFocusSession(FocusSession session) async {
    _sessions.add(session);
  }

  Future<List<FocusSession>> getFocusSessions() async {
    return List.from(_sessions);
  }

  Future<void> updateFocusSession(FocusSession session) async {
    final index = _sessions.indexWhere((s) => s.id == session.id);
    if (index != -1) {
      _sessions[index] = session;
    }
  }

  // Task operations
  Future<List<Task>> getTasksByType(TaskType type) async {
    if (type == TaskType.activation) {
      return List.from(_activationTasks);
    } else {
      return List.from(_breakTasks);
    }
  }

  Future<Task?> getTaskById(String id) async {
    final allTasks = [..._activationTasks, ..._breakTasks];
    try {
      return allTasks.firstWhere((task) => task.id == id);
    } catch (e) {
      return null;
    }
  }
} 