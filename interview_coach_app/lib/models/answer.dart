class AnswerModel {
  final String question;
  String answer;
  final String? audioPath;

  AnswerModel({required this.question, required this.answer, this.audioPath});

  Map<String, dynamic> toMap() => {
        'question': question,
        'answer': answer,
        'audio_path': audioPath,
      };

  factory AnswerModel.fromMap(Map<String, dynamic> m) {
    return AnswerModel(
      question: m['question'] ?? '',
      answer: m['answer'] ?? '',
      audioPath: m['audio_path'],
    );
  }
}
