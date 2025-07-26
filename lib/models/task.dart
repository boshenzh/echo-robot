class Task {
  final String id;
  final String title;
  final String description;
  final TaskType type;
  final int? durationMinutes;

  const Task({
    required this.id,
    required this.title,
    required this.description,
    required this.type,
    this.durationMinutes,
  });

  factory Task.fromJson(Map<String, dynamic> json) {
    return Task(
      id: json['id'] as String,
      title: json['title'] as String,
      description: json['description'] as String,
      type: TaskType.values.firstWhere(
        (e) => e.toString() == 'TaskType.${json['type']}',
      ),
      durationMinutes: json['durationMinutes'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'type': type.toString().split('.').last,
      'durationMinutes': durationMinutes,
    };
  }
}

enum TaskType {
  activation,
  breakTask,
} 