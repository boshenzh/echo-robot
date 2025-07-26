class FocusSession {
  final String id;
  final DateTime startTime;
  final DateTime endTime;
  final int durationMinutes;
  final bool completed;
  final String? activationTaskId;
  final String? breakTaskId;

  const FocusSession({
    required this.id,
    required this.startTime,
    required this.endTime,
    required this.durationMinutes,
    required this.completed,
    this.activationTaskId,
    this.breakTaskId,
  });

  factory FocusSession.fromJson(Map<String, dynamic> json) {
    return FocusSession(
      id: json['id'] as String,
      startTime: DateTime.parse(json['startTime'] as String),
      endTime: DateTime.parse(json['endTime'] as String),
      durationMinutes: json['durationMinutes'] as int,
      completed: json['completed'] as bool,
      activationTaskId: json['activationTaskId'] as String?,
      breakTaskId: json['breakTaskId'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'startTime': startTime.toIso8601String(),
      'endTime': endTime.toIso8601String(),
      'durationMinutes': durationMinutes,
      'completed': completed,
      'activationTaskId': activationTaskId,
      'breakTaskId': breakTaskId,
    };
  }

  Duration get duration => Duration(minutes: durationMinutes);
} 