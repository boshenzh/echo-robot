import 'dart:async';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:flutter/foundation.dart';
import '../models/focus_session.dart';
import '../models/task.dart';
import 'memory_storage_service.dart';

class DatabaseService {
  static Database? _database;
  final MemoryStorageService _memoryService = MemoryStorageService();

  Future<Database> get database async {
    if (kIsWeb) {
      throw UnsupportedError('Database not supported on web platform');
    }
    
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    String path = join(await getDatabasesPath(), 'focus_companion.db');
    return await openDatabase(
      path,
      version: 1,
      onCreate: _onCreate,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    // Focus sessions table
    await db.execute('''
      CREATE TABLE focus_sessions(
        id TEXT PRIMARY KEY,
        startTime TEXT NOT NULL,
        endTime TEXT NOT NULL,
        durationMinutes INTEGER NOT NULL,
        completed INTEGER NOT NULL,
        activationTaskId TEXT,
        breakTaskId TEXT
      )
    ''');

    // Tasks table
    await db.execute('''
      CREATE TABLE tasks(
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        type TEXT NOT NULL,
        durationMinutes INTEGER
      )
    ''');

    // Insert default tasks
    await _insertDefaultTasks(db);
    
    // Update existing tasks to Chinese
    await _updateTasksToChinese();
  }

  Future<void> _updateTasksToChinese() async {
    if (kIsWeb) {
      return;
    }
    
    final db = await database;
    
    // Update activation tasks
    await db.update(
      'tasks',
      {
        'title': '大声说出你看到的5样东西',
        'description': '环顾四周，说出你能在环境中看到的5个物体',
      },
      where: 'id = ?',
      whereArgs: ['act_1'],
    );
    
    await db.update(
      'tasks',
      {
        'title': '触摸周围的4种不同材质',
        'description': '找到并触摸你周围环境中的4种不同材质',
      },
      where: 'id = ?',
      whereArgs: ['act_2'],
    );
    
    await db.update(
      'tasks',
      {
        'title': '站起来伸展',
        'description': '站起来做30秒的轻柔伸展',
      },
      where: 'id = ?',
      whereArgs: ['act_3'],
    );
    
    await db.update(
      'tasks',
      {
        'title': '喝一杯水',
        'description': '花点时间专注地喝完一整杯水',
      },
      where: 'id = ?',
      whereArgs: ['act_4'],
    );
    
    await db.update(
      'tasks',
      {
        'title': '做3次深呼吸',
        'description': '舒适地坐着，做3次缓慢的深呼吸',
      },
      where: 'id = ?',
      whereArgs: ['act_5'],
    );
    
    // Update break tasks
    await db.update(
      'tasks',
      {
        'title': '看窗外1分钟',
        'description': '找到一扇窗户，观察外面的景色',
      },
      where: 'id = ?',
      whereArgs: ['break_1'],
    );
    
    await db.update(
      'tasks',
      {
        'title': '给植物浇水',
        'description': '照顾你空间里的一盆植物',
      },
      where: 'id = ?',
      whereArgs: ['break_2'],
    );
    
    await db.update(
      'tasks',
      {
        'title': '喝茶',
        'description': '专注地泡一杯茶并享受',
      },
      where: 'id = ?',
      whereArgs: ['break_3'],
    );
    
    await db.update(
      'tasks',
      {
        'title': '轻柔的颈部伸展',
        'description': '做一些轻柔的颈部和肩部伸展',
      },
      where: 'id = ?',
      whereArgs: ['break_4'],
    );
    
    await db.update(
      'tasks',
      {
        'title': '短暂外出',
        'description': '到外面待一会儿，感受空气',
      },
      where: 'id = ?',
      whereArgs: ['break_5'],
    );
  }

  Future<void> _insertDefaultTasks(Database db) async {
    final activationTasks = [
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
        description: '真的需要喝水',
        type: TaskType.activation,
      ),
      Task(
        id: 'act_5',
        title: '做3次深呼吸',
        description: '舒适地坐着，做3次缓慢的深呼吸',
        type: TaskType.activation,
      ),
    ];

    final breakTasks = [
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

    for (final task in [...activationTasks, ...breakTasks]) {
      await db.insert('tasks', task.toJson());
    }
  }

  // Focus Session operations
  Future<void> insertFocusSession(FocusSession session) async {
    if (kIsWeb) {
      await _memoryService.insertFocusSession(session);
      return;
    }
    
    final db = await database;
    await db.insert('focus_sessions', session.toJson());
  }

  Future<List<FocusSession>> getFocusSessions() async {
    if (kIsWeb) {
      return await _memoryService.getFocusSessions();
    }
    
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query('focus_sessions');
    return List.generate(maps.length, (i) => FocusSession.fromJson(maps[i]));
  }

  Future<void> updateFocusSession(FocusSession session) async {
    if (kIsWeb) {
      await _memoryService.updateFocusSession(session);
      return;
    }
    
    final db = await database;
    await db.update(
      'focus_sessions',
      session.toJson(),
      where: 'id = ?',
      whereArgs: [session.id],
    );
  }

  // Task operations
  Future<List<Task>> getTasksByType(TaskType type) async {
    if (kIsWeb) {
      return await _memoryService.getTasksByType(type);
    }
    
    final db = await database;
    
    // First, update tasks to Chinese if needed
    await _updateTasksToChinese();
    
    final List<Map<String, dynamic>> maps = await db.query(
      'tasks',
      where: 'type = ?',
      whereArgs: [type.toString().split('.').last],
    );
    return List.generate(maps.length, (i) => Task.fromJson(maps[i]));
  }

  Future<Task?> getTaskById(String id) async {
    if (kIsWeb) {
      return await _memoryService.getTaskById(id);
    }
    
    final db = await database;
    
    // First, update tasks to Chinese if needed
    await _updateTasksToChinese();
    
    final List<Map<String, dynamic>> maps = await db.query(
      'tasks',
      where: 'id = ?',
      whereArgs: [id],
    );
    if (maps.isNotEmpty) {
      return Task.fromJson(maps.first);
    }
    return null;
  }
} 