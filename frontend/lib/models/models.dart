class UserProfile {
  final int? age;
  final String? goals;
  final double? typicalSleepHours;
  final String? activityLevel;
  final String? scheduleType;

  UserProfile({this.age, this.goals, this.typicalSleepHours, this.activityLevel, this.scheduleType});

  Map<String, dynamic> toJson() => {
        'age': age,
        'goals': goals,
        'typical_sleep_hours': typicalSleepHours,
        'activity_level': activityLevel,
        'schedule_type': scheduleType,
      };
}

class Recommendation {
  final String id;
  final String priorityDimension;
  final String priorityReason;
  final String? llmExplanation;
  final bool safetyFlagged;
  final String? safetyMessage;
  final bool isCompleted;
  final List<RecommendationAction> actions;

  Recommendation({
    required this.id,
    required this.priorityDimension,
    required this.priorityReason,
    this.llmExplanation,
    this.safetyFlagged = false,
    this.safetyMessage,
    this.isCompleted = false,
    required this.actions,
  });

  factory Recommendation.fromJson(Map<String, dynamic> json) {
    var list = json['actions'] as List? ?? [];
    List<RecommendationAction> actionsList =
        list.map((i) => RecommendationAction.fromJson(i)).toList();
    return Recommendation(
      id: json['id'],
      priorityDimension: json['priority_dimension'],
      priorityReason: json['priority_reason'],
      llmExplanation: json['llm_explanation'],
      safetyFlagged: json['safety_flagged'] ?? false,
      safetyMessage: json['safety_message'],
      isCompleted: json['is_completed'] ?? false,
      actions: actionsList,
    );
  }
}

class RecommendationAction {
  final String id;
  final String actionText;
  final int order;
  final bool isCompleted;

  RecommendationAction({
    required this.id,
    required this.actionText,
    required this.order,
    this.isCompleted = false,
  });

  factory RecommendationAction.fromJson(Map<String, dynamic> json) {
    return RecommendationAction(
      id: json['id'],
      actionText: json['action_text'],
      order: json['order'],
      isCompleted: json['is_completed'] ?? false,
    );
  }
}

class CheckInResponse {
  final String checkInDate;
  
  CheckInResponse({required this.checkInDate});
  
  factory CheckInResponse.fromJson(Map<String, dynamic> json) {
    return CheckInResponse(checkInDate: json['check_in_date']);
  }
}
