// lib/screens/review_answers_screen.dart
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../api/sessions_api.dart';
import '../models/answer.dart';

class ReviewAnswersScreen extends StatefulWidget {
  const ReviewAnswersScreen({super.key});
  @override
  State<ReviewAnswersScreen> createState() => _ReviewAnswersScreenState();
}

class _ReviewAnswersScreenState extends State<ReviewAnswersScreen> {
  late int sessionId;
  late List<AnswerModel> answers;
  bool evaluating = false;

  Future<void> evaluateAllAndFetchResults() async {
    setState(() => evaluating = true);
    try {
      // ask backend to evaluate (bulk)
      await SessionsApi.evaluateAll(sessionId);

      // fetch final results (evaluations + raw)
      final res = await SessionsApi.getResults(sessionId);

      // Navigate to results/analysis screen with backend response map
      Navigator.pushNamed(context, '/results', arguments: res);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Evaluation failed: $e")));
    } finally {
      setState(() => evaluating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final args = ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
    sessionId = args['session_id'];
    answers = (args['answers'] as List).map((a) {
      if (a is AnswerModel) return a;
      if (a is Map<String,dynamic>) return AnswerModel.fromMap(a);
      return AnswerModel(question: a['question'] ?? '', answer: a['answer'] ?? '', audioPath: a['audio_path']);
    }).toList();

    return Scaffold(
      appBar: AppBar(title: const Text('Review Answers')),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(children: [
          Expanded(child: ListView.builder(itemCount: answers.length, itemBuilder: (_, i) {
            final a = answers[i];
            return Card(
              margin: const EdgeInsets.only(bottom: 10),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(a.question, style: GoogleFonts.poppins(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 8),
                  TextFormField(initialValue: a.answer, maxLines: 4, onChanged: (v) => a.answer = v),
                  if (a.audioPath != null) ...[
                    const SizedBox(height: 8),
                    Text('Audio: ${a.audioPath}', style: GoogleFonts.inter(color: Colors.grey[700])),
                  ]
                ]),
              ),
            );
          })),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: evaluating ? null : evaluateAllAndFetchResults,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF4D9DE0),
                padding: const EdgeInsets.symmetric(vertical: 16),
                textStyle: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
              ),
              child: evaluating ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Text('Evaluate My Answers', style: TextStyle(color: Colors.white)),
            ),
          ),
        ]),
      ),
    );
  }
}
