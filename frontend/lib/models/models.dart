class UserProfile {
  final int? age;
  final String? goals;
  final double? typicalSleepHours;
  final String? activityLevel;
  final String? scheduleType;
  final double? goalSleepHours;
  final int? goalWaterGlasses;
  final int? goalActivityMinutes;
  final double? goalMaxScreenHours;
  final int? goalMaxCaffeineCups;

  UserProfile({
    this.age,
    this.goals,
    this.typicalSleepHours,
    this.activityLevel,
    this.scheduleType,
    this.goalSleepHours,
    this.goalWaterGlasses,
    this.goalActivityMinutes,
    this.goalMaxScreenHours,
    this.goalMaxCaffeineCups,
  });

  Map<String, dynamic> toJson() => {
        'age': age,
        'goals': goals,
        'typical_sleep_hours': typicalSleepHours,
        'activity_level': activityLevel,
        'schedule_type': scheduleType,
        'goal_sleep_hours': goalSleepHours,
        'goal_water_glasses': goalWaterGlasses,
        'goal_activity_minutes': goalActivityMinutes,
        'goal_max_screen_hours': goalMaxScreenHours,
        'goal_max_caffeine_cups': goalMaxCaffeineCups,
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

class StreakData {
  final int currentStreak;
  final int longestStreak;
  final int goalsMetStreak;
  final String message;

  StreakData({
    required this.currentStreak,
    required this.longestStreak,
    required this.goalsMetStreak,
    required this.message,
  });

  factory StreakData.fromJson(Map<String, dynamic> json) {
    return StreakData(
      currentStreak: json['current_checkin_streak'] ?? 0,
      longestStreak: json['longest_checkin_streak'] ?? 0,
      goalsMetStreak: json['goals_met_streak'] ?? 0,
      message: json['message'] ?? '',
    );
  }
}

class DimensionTrend {
  final String dimension;
  final double? thisWeekAvg;
  final double? lastWeekAvg;
  final String direction; // improving | declining | stable | no_data

  DimensionTrend({
    required this.dimension,
    this.thisWeekAvg,
    this.lastWeekAvg,
    required this.direction,
  });

  factory DimensionTrend.fromJson(Map<String, dynamic> json) {
    return DimensionTrend(
      dimension: json['dimension'],
      thisWeekAvg: (json['this_week_avg'] as num?)?.toDouble(),
      lastWeekAvg: (json['last_week_avg'] as num?)?.toDouble(),
      direction: json['direction'] ?? 'no_data',
    );
  }
}

class TrendsData {
  final List<DimensionTrend> trends;

  TrendsData({required this.trends});

  factory TrendsData.fromJson(Map<String, dynamic> json) {
    var list = json['trends'] as List? ?? [];
    return TrendsData(
      trends: list.map((i) => DimensionTrend.fromJson(i)).toList(),
    );
  }
}

class DailyGoals {
  final double? goalSleepHours;
  final int? goalWaterGlasses;
  final int? goalActivityMinutes;
  final double? goalMaxScreenHours;
  final int? goalMaxCaffeineCups;

  DailyGoals({
    this.goalSleepHours,
    this.goalWaterGlasses,
    this.goalActivityMinutes,
    this.goalMaxScreenHours,
    this.goalMaxCaffeineCups,
  });

  Map<String, dynamic> toJson() => {
        if (goalSleepHours != null) 'goal_sleep_hours': goalSleepHours,
        if (goalWaterGlasses != null) 'goal_water_glasses': goalWaterGlasses,
        if (goalActivityMinutes != null) 'goal_activity_minutes': goalActivityMinutes,
        if (goalMaxScreenHours != null) 'goal_max_screen_hours': goalMaxScreenHours,
        if (goalMaxCaffeineCups != null) 'goal_max_caffeine_cups': goalMaxCaffeineCups,
      };
}
