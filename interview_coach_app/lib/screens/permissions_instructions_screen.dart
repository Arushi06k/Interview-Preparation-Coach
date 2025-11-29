import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:permission_handler/permission_handler.dart';
import '../api/sessions_api.dart';

class PermissionsInstructionsScreen extends StatefulWidget {
  const PermissionsInstructionsScreen({super.key});
  @override
  State<PermissionsInstructionsScreen> createState() => _PermissionsInstructionsScreenState();
}

class _PermissionsInstructionsScreenState extends State<PermissionsInstructionsScreen> {
  bool micGranted = false;
  bool camGranted = false;
  bool loading = false;

  Future<void> requestPermissions() async {
    if (!kIsWeb && (Platform.isAndroid || Platform.isIOS)) {
      final mic = await Permission.microphone.request();
      final cam = await Permission.camera.request();
      setState(() {
        micGranted = mic.isGranted;
        camGranted = cam.isGranted;
      });
    } else {
      // Desktop/web: still allow flow but recording will be disabled
      setState(() {
        micGranted = false;
        camGranted = false;
      });
    }
  }

  // Create session on backend and generate questions, then navigate
  Future<void> createSessionAndStart(Map<String, dynamic> payload) async {
    setState(() => loading = true);
    try {
      // Create session on backend
      final session = await SessionsApi.createSession(payload);
      final int sessionId = session['id'] is int ? session['id'] as int : int.parse(session['id'].toString());

      // Generate questions for that session
      final questions = await SessionsApi.generateQuestions(sessionId);

      // Navigate to question list with sessionId and questions
      Navigator.pushNamedAndRemoveUntil(
        context,
        '/question_list',
        (route) => true,
        arguments: {'session_id': sessionId, 'questions': questions},
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to start session: $e')));
    } finally {
      setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final incoming = ModalRoute.of(context)?.settings.arguments;
    final Map<String, dynamic> payload = (incoming is Map<String, dynamic>) ? incoming : {};

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(colors: [Color(0xFF4D9DE0), Color(0xFF87CEFA)], begin: Alignment.topLeft, end: Alignment.bottomRight),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text("Ready?", style: GoogleFonts.poppins(fontSize: 26, color: Colors.white, fontWeight: FontWeight.w800)),
              const SizedBox(height: 12),

              const Card(
                child: Padding(
                  padding: EdgeInsets.all(12),
                  child: Column(children: [
                    ListTile(leading: Icon(Icons.timer), title: Text("Each question has a suggested time. Stay concise.")),
                    ListTile(leading: Icon(Icons.volume_up), title: Text("Speak clearly, avoid background noise.")),
                    ListTile(leading: Icon(Icons.text_fields), title: Text("You can type your answer in the text box too.")),
                    ListTile(leading: Icon(Icons.camera_alt), title: Text("Camera access is optional and used for facial analysis.")),
                  ]),
                ),
              ),

              const SizedBox(height: 12),

              ElevatedButton(
                onPressed: requestPermissions,
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF4D9DE0)),
                child: const Text("Request Permissions"),
              ),

              const SizedBox(height: 10),

              Text("Microphone: ${micGranted ? 'Granted' : 'Not granted'}", style: const TextStyle(color: Colors.white)),
              Text("Camera: ${camGranted ? 'Granted' : 'Not granted'}", style: const TextStyle(color: Colors.white)),

              const Spacer(),

              // Start Interview — creates session, generate questions, then navigates
              ElevatedButton(
                onPressed: loading
                    ? null
                    : () {
                        // Ensure payload contains selected_domain & difficulty_level.
                        if (payload['selected_domain'] == null) {
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Missing domain selection. Go back and select a domain.')));
                          return;
                        }
                        // Create session and start
                        createSessionAndStart(payload);
                      },
                style: ElevatedButton.styleFrom(backgroundColor: Colors.white, foregroundColor: const Color(0xFF4D9DE0), padding: const EdgeInsets.symmetric(vertical: 14)),
                child: loading ? const SizedBox(height: 20, width: 23, child: CircularProgressIndicator(color: Color(0xFF4D9DE0), strokeWidth: 2)) : const Text("Start Interview", style: TextStyle(fontWeight: FontWeight.bold)),
              ),
            ]),
          ),
        ),
      ),
    );
  }
}
