import 'dart:async';
import 'dart:math';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../models/focus_session.dart';
import '../models/task.dart';
import '../services/database_service.dart';

part 'app_state.g.dart';

enum AppScreen {
  home,
  activation,
  focusSetup,
  focus,
  breakScreen,
}

@riverpod
class AppState extends _$AppState {
  Timer? _timer;
  DateTime? _sessionStartTime;

  @override
  AppScreen build() {
    return AppScreen.home;
  }

  void navigateTo(AppScreen screen) {
    state = screen;
  }

  void startActivation() {
    state = AppScreen.activation;
  }

  void completeActivation() {
    state = AppScreen.focusSetup;
  }

  void startFocusSession(int durationMinutes) {
    _sessionStartTime = DateTime.now();
    final endTime = _sessionStartTime!.add(Duration(minutes: durationMinutes));
    
    // Create focus session
    final session = FocusSession(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      startTime: _sessionStartTime!,
      endTime: endTime,
      durationMinutes: durationMinutes,
      completed: false,
    );
    
    // Save to database
    ref.read(databaseServiceProvider).insertFocusSession(session);
    
    state = AppScreen.focus;
  }

  void completeFocusSession() {
    _timer?.cancel();
    state = AppScreen.breakScreen;
  }

  void completeBreak() {
    state = AppScreen.home;
  }

  void goHome() {
    _timer?.cancel();
    state = AppScreen.home;
  }

  void dispose() {
    _timer?.cancel();
  }
}

@riverpod
Future<Task> randomActivationTask(RandomActivationTaskRef ref) async {
  final tasks = await ref.watch(activationTasksProvider.future);
  final random = Random();
  return tasks[random.nextInt(tasks.length)];
}

@riverpod
Future<Task> randomBreakTask(RandomBreakTaskRef ref) async {
  final tasks = await ref.watch(breakTasksProvider.future);
  final random = Random();
  return tasks[random.nextInt(tasks.length)];
}

@riverpod
Future<List<Task>> activationTasks(ActivationTasksRef ref) async {
  final dbService = ref.watch(databaseServiceProvider);
  return await dbService.getTasksByType(TaskType.activation);
}

@riverpod
Future<List<Task>> breakTasks(BreakTasksRef ref) async {
  final dbService = ref.watch(databaseServiceProvider);
  return await dbService.getTasksByType(TaskType.breakTask);
}

@riverpod
DatabaseService databaseService(DatabaseServiceRef ref) {
  return DatabaseService();
}

@riverpod
class FocusTimer extends _$FocusTimer {
  Timer? _timer;
  DateTime? _startTime;
  int _durationMinutes = 0;

  @override
  Duration build() {
    return Duration.zero;
  }

  void start(int durationMinutes) {
    _durationMinutes = durationMinutes;
    _startTime = DateTime.now();
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      final elapsed = DateTime.now().difference(_startTime!);
      final remaining = Duration(minutes: _durationMinutes) - elapsed;
      
      if (remaining.isNegative) {
        timer.cancel();
        state = Duration.zero;
        ref.read(appStateProvider.notifier).completeFocusSession();
      } else {
        state = remaining;
      }
    });
  }

  void pause() {
    _timer?.cancel();
  }

  void resume() {
    if (_startTime != null) {
      start(_durationMinutes);
    }
  }

  void stop() {
    _timer?.cancel();
    state = Duration.zero;
  }

  void dispose() {
    _timer?.cancel();
  }
}

@riverpod
class BreakTimer extends _$BreakTimer {
  Timer? _timer;
  DateTime? _startTime;
  int _durationMinutes = 0;

  @override
  Duration build() {
    return Duration.zero;
  }

  void start(int durationMinutes) {
    _durationMinutes = durationMinutes;
    _startTime = DateTime.now();
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      final elapsed = DateTime.now().difference(_startTime!);
      final remaining = Duration(minutes: _durationMinutes) - elapsed;
      
      if (remaining.isNegative) {
        timer.cancel();
        state = Duration.zero;
        ref.read(appStateProvider.notifier).completeBreak();
      } else {
        state = remaining;
      }
    });
  }

  void stop() {
    _timer?.cancel();
    state = Duration.zero;
  }

  void dispose() {
    _timer?.cancel();
  }
} 