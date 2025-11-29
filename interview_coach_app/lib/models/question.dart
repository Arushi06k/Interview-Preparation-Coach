class QuestionModel {
  final String id;
  final String question;
  final List<dynamic> keywords;

  QuestionModel({required this.id, required this.question, required this.keywords});

  factory QuestionModel.fromMap(Map<String, dynamic> m) {
    return QuestionModel(
      id: (m['id'] ?? '').toString(),
      question: m['question'] ?? '',
      keywords: List<dynamic>.from(m['keywords'] ?? []),
    );
  }
}
