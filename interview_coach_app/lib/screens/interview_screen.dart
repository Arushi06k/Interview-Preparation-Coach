// lib/screens/interview_screen.dart
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'package:record/record.dart'; // NEW API (6.x)

import '../api/sessions_api.dart';
import '../models/answer.dart';

class InterviewScreen extends StatefulWidget {
  const InterviewScreen({super.key});
  @override
  State<InterviewScreen> createState() => _InterviewScreenState();
}

class _InterviewScreenState extends State<InterviewScreen>
    with SingleTickerProviderStateMixin {
  late List<dynamic> questions;
  late int sessionId;

  int index = 0;
  bool recording = false;
  bool saving = false;

  // NEW API
  final AudioRecorder recorder = AudioRecorder();

  final TextEditingController textController = TextEditingController();
  String? tempAudioPath;
  final List<AnswerModel> answersBuffer = [];

  late AnimationController pulse;

  @override
  void initState() {
    super.initState();
    pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    pulse.dispose();
    textController.dispose();
    recorder.dispose();
    super.dispose();
  }

  bool get isDesktop {
    if (kIsWeb) return true;
    return Platform.isWindows || Platform.isLinux || Platform.isMacOS;
  }

  // -----------------------------------------------------------
  // 🔥 NEW RECORDING METHOD — compatible with record ^6.x
  // -----------------------------------------------------------
  Future<void> toggleRecord() async {
    if (isDesktop) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text("Recording is available on Android/iOS only.")));
      return;
    }

    if (!recording) {
      // Request permission
      final hasPerm = await recorder.hasPermission();
      if (!hasPerm) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Microphone permission required")));
        return;
      }

      // Create temporary file path
      final dir = (await Directory.systemTemp.createTemp()).path;
      final path = '$dir/${DateTime.now().millisecondsSinceEpoch}.m4a';

      // Start recording (NEW API)
      await recorder.start(
        const RecordConfig(
          encoder: AudioEncoder.aacLc,
          bitRate: 128000,
          sampleRate: 44100,
        ),
        path: path,
      );

      setState(() => recording = true);
    } else {
      // Stop recording
      final path = await recorder.stop();

      setState(() => recording = false);
      tempAudioPath = path;

      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Recording saved")));
    }
  }

  // -----------------------------------------------------------
  // SAVE current answer to backend + local buffer
  // -----------------------------------------------------------
  Future<void> saveAndNext() async {
    if (saving) return;
    setState(() => saving = true);

    final qtext = questions[index]["question"] ?? "";
    final typed = textController.text.trim();

    final localAns =
        AnswerModel(question: qtext, answer: typed, audioPath: tempAudioPath);

    if (index < answersBuffer.length) {
      answersBuffer[index] = localAns;
    } else {
      answersBuffer.add(localAns);
    }

    tempAudioPath = null;
    textController.clear();

    try {
      // Save raw answer to backend
      await SessionsApi.saveAnswer(sessionId, qtext.toString(), typed);

      if (index < questions.length - 1) {
        setState(() => index++);
        if (index < answersBuffer.length) {
          textController.text = answersBuffer[index].answer;
        }
      } else {
        // All questions completed → review page
        Navigator.pushNamed(context, '/review',
            arguments: {
              'session_id': sessionId,
              'answers': answersBuffer,
            });
      }
    } catch (e) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text("Save failed: $e")));
    }

    setState(() => saving = false);
  }

  @override
  Widget build(BuildContext context) {
    final args =
        ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;

    sessionId = args['session_id'];

    // Normalize questions so unexpected shapes don’t break UI
    questions = (args['questions'] as List)
        .map((e) {
          if (e is Map<String, dynamic>) return e;
          return {"question": e.toString(), "keywords_str": ""};
        })
        .toList();

    final total = questions.length;
    final q = questions[index]["question"] ?? "";

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF4D9DE0), Color(0xFF87CEFA)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              children: [
                // HEADER
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text("Interview",
                        style: GoogleFonts.poppins(
                            color: Colors.white,
                            fontSize: 26,
                            fontWeight: FontWeight.w800)),
                    Text("${index + 1} / $total",
                        style: GoogleFonts.poppins(
                            color: Colors.white,
                            fontWeight: FontWeight.w600)),
                  ],
                ),

                const SizedBox(height: 10),
                LinearProgressIndicator(
                  value: (index + 1) / total,
                  backgroundColor: Colors.white30,
                  color: Colors.white,
                  minHeight: 6,
                ),

                const SizedBox(height: 16),

                // QUESTION CARD
                Expanded(
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(22),
                      boxShadow: const [
                        BoxShadow(
                            color: Colors.black12,
                            blurRadius: 12,
                            offset: Offset(0, 6))
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text("Question ${index + 1}",
                            style: GoogleFonts.poppins(
                                fontWeight: FontWeight.w700, fontSize: 18)),
                        const SizedBox(height: 14),
                        Expanded(
                            child: SingleChildScrollView(
                                child: Text(q,
                                    style: GoogleFonts.inter(
                                        fontSize: 18, height: 1.4)))),
                        const SizedBox(height: 12),
                        Text("Tip: Keep answers clear and structured.",
                            style: GoogleFonts.inter(
                                fontSize: 13, color: Colors.grey[600])),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 12),

                // TEXT ANSWER
                TextField(
                  controller: textController,
                  minLines: 2,
                  maxLines: 6,
                  decoration: InputDecoration(
                    hintText: "Type your answer here (you can edit later)",
                    filled: true,
                    fillColor: Colors.white,
                    border:
                        OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),

                const SizedBox(height: 10),

                // RECORD + NEXT BUTTONS
                Row(
                  children: [
                    ElevatedButton.icon(
                      onPressed: toggleRecord,
                      icon: Icon(recording ? Icons.stop : Icons.mic),
                      label: Text(recording ? "Stop" : "Record"),
                      style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.white,
                          foregroundColor: const Color(0xFF4D9DE0)),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: saving ? null : saveAndNext,
                        style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF4D9DE0),
                            padding: const EdgeInsets.symmetric(vertical: 14)),
                        child: saving
                            ? const SizedBox(
                                height: 18,
                                width: 18,
                                child: CircularProgressIndicator(
                                    color: Colors.white, strokeWidth: 2),
                              )
                            : Text(
                                index < questions.length - 1
                                    ? "Save & Next"
                                    : "Review Answers",
                                style: const TextStyle(color: Colors.white),
                              ),
                      ),
                    )
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
