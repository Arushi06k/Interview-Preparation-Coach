class SessionModel {
  final int id;
  final String selectedDomain;
  final String difficultyLevel;

  SessionModel({required this.id, required this.selectedDomain, required this.difficultyLevel});

  factory SessionModel.fromMap(Map<String, dynamic> m) {
    return SessionModel(
      id: m['id'] ?? 0,
      selectedDomain: m['selected_domain'] ?? '',
      difficultyLevel: m['difficulty_level'] ?? '',
    );
  }
}
