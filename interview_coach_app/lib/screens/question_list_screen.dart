// lib/screens/question_list_screen.dart
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:permission_handler/permission_handler.dart';
import '../widgets/primary_button.dart';

class QuestionListScreen extends StatefulWidget {
  const QuestionListScreen({super.key});

  @override
  State<QuestionListScreen> createState() => _QuestionListScreenState();
}

class _QuestionListScreenState extends State<QuestionListScreen> {
  bool micGranted = false;
  bool camGranted = false;

  Future<void> _checkPermissions() async {
    final mic = await Permission.microphone.status;
    final cam = await Permission.camera.status;

    setState(() {
      micGranted = mic.isGranted;
      camGranted = cam.isGranted;
    });
  }

  Future<void> _requestPermissions() async {
    final mic = await Permission.microphone.request();
    final cam = await Permission.camera.request();

    setState(() {
      micGranted = mic.isGranted;
      camGranted = cam.isGranted;
    });
  }

  Future<void> _startInterview() async {
  final args =
      ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;

  final int sessionId = args['session_id'];

  // ---- FIX BEGIN ----
  final dynamic raw = args['questions'];

  // Case 1: Already a List
  List questionsList;
  if (raw is List) {
    questionsList = raw;
  }
  // Case 2: Wrapped inside { "questions": [...] }
  else if (raw is Map && raw['questions'] is List) {
    questionsList = raw['questions'];
  }
  // Case 3: Anything else = error fallback
  else {
    throw Exception("Invalid questions format: $raw");
  }

  // Normalize each item to map
  final questions = questionsList.map((e) {
    if (e is Map<String, dynamic>) return e;
    return {
      "question": e.toString(),
      "keywords": [],
    };
  }).toList();
  // ---- FIX END ----

  Navigator.pushNamed(
    context,
    "/interview",
    arguments: {
      "session_id": sessionId,
      "questions": questions,
    },
  );
}


  @override
  void initState() {
    super.initState();
    _checkPermissions();
  }

  @override
  Widget build(BuildContext context) {
    final args =
        ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;

    final int sessionId = args['session_id'];

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
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("Ready?",
                    style: GoogleFonts.poppins(
                        fontSize: 28,
                        fontWeight: FontWeight.w800,
                        color: Colors.white)),

                const SizedBox(height: 18),

                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(18),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _item(Icons.timer, "Each question has a suggested time."),
                      _item(Icons.mic, "Speak clearly, avoid background noise."),
                      _item(Icons.keyboard, "You may also type your answers."),
                      _item(Icons.camera_alt,
                          "Camera is optional for facial analysis."),
                    ],
                  ),
                ),

                const SizedBox(height: 20),

                Text(
                  "Microphone: ${micGranted ? "Granted" : "Not granted"}",
                  style: GoogleFonts.inter(color: Colors.white, fontSize: 16),
                ),
                Text(
                  "Camera: ${camGranted ? "Granted" : "Not granted"}",
                  style: GoogleFonts.inter(color: Colors.white, fontSize: 16),
                ),

                const Spacer(),

                // Request permissions button
                PrimaryButton(
                  text: "Grant Permissions",
                  onPressed: _requestPermissions,
                ),

                const SizedBox(height: 10),

                // START INTERVIEW BUTTON
                PrimaryButton(
                  text: "Start Interview",
                  onPressed: (micGranted) ? _startInterview : null,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _item(IconData icon, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          Icon(icon, color: Colors.black87),
          const SizedBox(width: 10),
          Expanded(
            child: Text(text,
                style: GoogleFonts.inter(fontSize: 15, height: 1.3)),
          ),
        ],
      ),
    );
  }
}
