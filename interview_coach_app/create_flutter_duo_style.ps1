# Save this as create_flutter_duo_style.ps1 and run in the root of interview_coach_app
# Example: PS> .\create_flutter_duo_style.ps1

Write-Host "Creating Duolingo-style Flutter app files..."

# PUBSPEC
$pubspec = @"
name: interview_coach_app
description: Automated Interview Prep Coach - Duolingo-style (Purple-Pink Gradient)
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: ">=2.18.0 <4.0.0"

dependencies:
  flutter:
    sdk: flutter

  dio: ^5.4.0
  file_picker: ^6.1.1
  path_provider: ^2.1.3
  record: ^5.0.0
  camera: ^0.10.5+9
  fl_chart: ^0.68.0
  google_fonts: ^6.2.1
  flutter_svg: ^2.0.10+1
  animations: ^2.0.11
  uuid: ^4.4.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0

flutter:
  uses-material-design: true
  assets:
    - assets/images/
"@

Set-Content -Path .\pubspec.yaml -Value $pubspec -Encoding UTF8
Write-Host "Wrote pubspec.yaml"

# Create folders
$folders = @("lib","lib/api","lib/models","lib/screens","lib/widgets","assets","assets/images")
foreach ($f in $folders) {
    if (-not (Test-Path $f)) { New-Item -ItemType Directory -Path $f | Out-Null }
}

# API: api_client.dart
$api_client = @"
import 'package:dio/dio.dart';

class ApiClient {
  static final Dio dio = Dio(
    BaseOptions(
      baseUrl: 'http://YOUR_LOCAL_IP:8000/api', // <<-- CHANGE THIS to your backend IP
      connectTimeout: const Duration(seconds: 12),
      receiveTimeout: const Duration(seconds: 25),
      headers: {'Accept': 'application/json'},
    ),
  );
}
"@
Set-Content -Path .\lib\api\api_client.dart -Value $api_client -Encoding UTF8

# API: resume_api.dart
$resume_api = @"
import 'dart:io';
import 'package:dio/dio.dart';
import 'api_client.dart';

class ResumeApi {
  static Future<Map<String, dynamic>> uploadResume(File file) async {
    final form = FormData.fromMap({
      'resume': await MultipartFile.fromFile(file.path, filename: file.path.split('/').last)
    });

    final resp = await ApiClient.dio.post('/get-domains', data: form);
    return Map<String, dynamic>.from(resp.data);
  }
}
"@
Set-Content -Path .\lib\api\resume_api.dart -Value $resume_api -Encoding UTF8

# API: sessions_api.dart
$sessions_api = @"
import 'package:dio/dio.dart';
import 'api_client.dart';

class SessionsApi {
  static Future<Map<String, dynamic>> createSession(Map<String, dynamic> payload) async {
    final res = await ApiClient.dio.post('/sessions', data: payload);
    return Map<String, dynamic>.from(res.data);
  }

  static Future<List<dynamic>> generateQuestions(int sessionId) async {
    final res = await ApiClient.dio.post('/sessions/$sessionId/generate-questions');
    return List<dynamic>.from(res.data['questions'] ?? []);
  }

  static Future<Map<String, dynamic>> saveAnswer(int sessionId, String question, String answer) async {
    final res = await ApiClient.dio.post('/sessions/$sessionId/save-answer', data: {
      'question': question,
      'answer': answer,
    });
    return Map<String, dynamic>.from(res.data);
  }

  static Future<Map<String, dynamic>> evaluateAll(int sessionId) async {
    final res = await ApiClient.dio.post('/sessions/$sessionId/evaluate-all');
    return Map<String, dynamic>.from(res.data);
  }

  static Future<Map<String, dynamic>> getResults(int sessionId) async {
    final res = await ApiClient.dio.get('/sessions/$sessionId/results');
    return Map<String, dynamic>.from(res.data);
  }
}
"@
Set-Content -Path .\lib\api\sessions_api.dart -Value $sessions_api -Encoding UTF8

# models/domain.dart
$domain_model = @"
class DomainModel {
  final String filename;
  final List<dynamic> topDomains;

  DomainModel({required this.filename, required this.topDomains});

  factory DomainModel.fromMap(Map<String, dynamic> m) {
    return DomainModel(
      filename: m['filename'] ?? '',
      topDomains: List<dynamic>.from(m['top_domains'] ?? []),
    );
  }
}
"@
Set-Content -Path .\lib\models\domain.dart -Value $domain_model -Encoding UTF8

# models/question.dart
$question_model = @"
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
"@
Set-Content -Path .\lib\models\question.dart -Value $question_model -Encoding UTF8

# models/session.dart
$session_model = @"
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
"@
Set-Content -Path .\lib\models\session.dart -Value $session_model -Encoding UTF8

# models/answer.dart
$answer_model = @"
class AnswerModel {
  final String question;
  final String answer;

  AnswerModel({required this.question, required this.answer});

  Map<String, dynamic> toMap() => {'question': question, 'answer': answer};
}
"@
Set-Content -Path .\lib\models\answer.dart -Value $answer_model -Encoding UTF8

# widgets/primary_button.dart
$primary_button = @"
import 'package:flutter/material.dart';

class PrimaryButton extends StatelessWidget {
  final String text;
  final VoidCallback onPressed;
  final bool loading;

  const PrimaryButton({required this.text, required this.onPressed, this.loading=false, Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: loading ? null : onPressed,
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        elevation: 8,
      ),
      child: loading
        ? SizedBox(height:18, width:18, child: CircularProgressIndicator(color: Colors.white, strokeWidth:2))
        : Text(text, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
    );
  }
}
"@
Set-Content -Path .\lib\widgets\primary_button.dart -Value $primary_button -Encoding UTF8

# widgets/duo_avatar.dart
$duo_avatar = @"
import 'package:flutter/material.dart';

class DuoAvatar extends StatelessWidget {
  final double size;
  const DuoAvatar({this.size = 84, Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Placeholder circle; replace with mascot PNG in assets/images/mascot.png
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [Color(0xFF8359FF), Color(0xFFFF5EAB)]),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 10, offset: Offset(0,6))],
      ),
      child: Center(child: Text('😊', style: TextStyle(fontSize: size/2))),
    );
  }
}
"@
Set-Content -Path .\lib\widgets\duo_avatar.dart -Value $duo_avatar -Encoding UTF8

# screens: splash_screen.dart
$splash = @"
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../widgets/duo_avatar.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({Key? key}) : super(key: key);
  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    Future.delayed(Duration(milliseconds: 900), () {
      Navigator.pushReplacementNamed(context, '/resume');
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(gradient: LinearGradient(colors: [Color(0xFF8359FF), Color(0xFFFF5EAB)], begin: Alignment.topLeft, end: Alignment.bottomRight)),
        child: Center(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            DuoAvatar(size: 120),
            SizedBox(height: 22),
            Text('Interview Coach', style: GoogleFonts.poppins(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w800)),
            SizedBox(height: 8),
            Text('Practice. Improve. Land the job.', style: GoogleFonts.inter(color: Colors.white70)),
          ]),
        ),
      ),
    );
  }
}
"@
Set-Content -Path .\lib\screens\splash_screen.dart -Value $splash -Encoding UTF8

# screens: resume_upload_screen.dart
$resume_screen = @"
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:google_fonts/google_fonts.dart';
import '../api/resume_api.dart';
import '../models/domain.dart';
import '../widgets/primary_button.dart';
import '../widgets/duo_avatar.dart';

class ResumeUploadScreen extends StatefulWidget {
  const ResumeUploadScreen({Key? key}) : super(key: key);
  @override
  State<ResumeUploadScreen> createState() => _ResumeUploadScreenState();
}

class _ResumeUploadScreenState extends State<ResumeUploadScreen> {
  File? _file;
  bool _loading = false;

  Future<void> pickFile() async {
    final res = await FilePicker.platform.pickFiles(type: FileType.custom, allowedExtensions: ['pdf','docx']);
    if (res == null) return;
    setState(() { _file = File(res.files.single.path!); });
  }

  Future<void> upload() async {
    if (_file == null) { ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Pick a resume first'))); return; }
    setState(() => _loading = true);
    try {
      final map = await ResumeApi.uploadResume(_file!);
      final dm = DomainModel.fromMap(map);
      Navigator.pushNamed(context, '/domain_select', arguments: dm);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Upload failed: \$e')));
    } finally { setState(() => _loading = false); }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(gradient: LinearGradient(colors: [Color(0xFF8359FF), Color(0xFFFF5EAB)], begin: Alignment.topLeft, end: Alignment.bottomRight)),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(18.0),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [DuoAvatar(size: 56), SizedBox(width:12), Text('Hello, Buddy', style: GoogleFonts.poppins(color: Colors.white, fontWeight: FontWeight.w700))]),
              SizedBox(height: 22),
              Text('Step 1', style: GoogleFonts.poppins(color: Colors.white70)),
              SizedBox(height: 8),
              Text('Upload your resume', style: GoogleFonts.poppins(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w800)),
              SizedBox(height: 18),
              Expanded(
                child: Container(
                  width: double.infinity,
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(22)),
                  padding: EdgeInsets.all(18),
                  child: Column(children: [
                    Icon(Icons.upload_file, size: 72, color: Color(0xFF8359FF)),
                    SizedBox(height: 12),
                    Text(_file==null? 'No file selected' : _file!.path.split('/').last, style: TextStyle(fontWeight: FontWeight.w600)),
                    SizedBox(height: 16),
                    ElevatedButton(onPressed: pickFile, child: Text('Pick PDF or DOCX')),
                    Spacer(),
                    PrimaryButton(text: 'Upload & Continue', onPressed: upload, loading: _loading),
                  ]),
                ),
              ),
            ]),
          ),
        ),
      ),
    );
  }
}
"@
Set-Content -Path .\lib\screens\resume_upload_screen.dart -Value $resume_screen -Encoding UTF8

# screens: domain_select_screen.dart
$domain_select = @"
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/domain.dart';
import '../widgets/primary_button.dart';
import '../api/sessions_api.dart';
import '../widgets/duo_avatar.dart';

class DomainSelectScreen extends StatefulWidget {
  const DomainSelectScreen({Key? key}) : super(key: key);
  @override
  State<DomainSelectScreen> createState() => _DomainSelectScreenState();
}

class _DomainSelectScreenState extends State<DomainSelectScreen> {
  String? selected;
  bool loading = false;

  @override
  Widget build(BuildContext context) {
    final dm = ModalRoute.of(context)!.settings.arguments as DomainModel;
    final domains = dm.topDomains;
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(gradient: LinearGradient(colors: [Color(0xFF8359FF), Color(0xFFFF5EAB)], begin: Alignment.topLeft, end: Alignment.bottomRight)),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(18.0),
            child: Column(children: [
              Row(children: [DuoAvatar(size:56), SizedBox(width:12), Text('Pick a focus', style: GoogleFonts.poppins(color: Colors.white, fontWeight: FontWeight.w700))]),
              SizedBox(height: 18),
              Expanded(
                child: Container(
                  width: double.infinity, decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(22)), padding: EdgeInsets.all(16),
                  child: Column(children: [
                    Text('Detected domains', style: GoogleFonts.poppins(fontWeight: FontWeight.w700)),
                    SizedBox(height: 12),
                    Expanded(
                      child: ListView.separated(
                        separatorBuilder: (_,__) => SizedBox(height:10),
                        itemCount: domains.length,
                        itemBuilder: (c,i) {
                          final d = domains[i].toString();
                          return GestureDetector(
                            onTap: () => setState(() => selected = d),
                            child: Container(
                              padding: EdgeInsets.symmetric(vertical:14, horizontal:16),
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(14),
                                color: selected==d? Color(0xFF8359FF).withOpacity(0.12) : Colors.grey[100],
                              ),
                              child: Row(children: [Expanded(child: Text(d, style: TextStyle(fontWeight: FontWeight.w600))), if (selected==d) Icon(Icons.check_circle, color: Color(0xFF8359FF))]),
                            ),
                          );
                        },
                      ),
                    ),
                    SizedBox(height:12),
                    PrimaryButton(
                      text: 'Create Session & Generate',
                      loading: loading,
                      onPressed: () async {
                        if (selected==null) { ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Select a domain'))); return; }
                        setState(() => loading = true);
                        try {
                          final payload = {'selected_domain': selected, 'difficulty_level': 'medium', 'resume_analysis_result': {'filename': dm.filename, 'top_domains': dm.topDomains}};
                          final session = await SessionsApi.createSession(payload);
                          final questions = await SessionsApi.generateQuestions(session['id']);
                          Navigator.pushNamed(context, '/question_list', arguments: {'session_id': session['id'], 'questions': questions});
                        } catch (e) {
                          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed: \$e')));
                        } finally { setState(() => loading = false); }
                      },
                    )
                  ]),
                ),
              )
            ]),
          ),
        ),
      ),
    );
  }
}
"@
Set-Content -Path .\lib\screens\domain_select_screen.dart -Value $domain_select -Encoding UTF8

# screens: question_list_screen.dart
$question_list = @"
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../widgets/primary_button.dart';

class QuestionListScreen extends StatelessWidget {
  const QuestionListScreen({Key? key}) : super(key: key);
  @override
  Widget build(BuildContext context) {
    final args = ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
    final int sessionId = args['session_id'];
    final List<dynamic> questions = args['questions'];

    return Scaffold(
      appBar: AppBar(title: Text('Questions', style: GoogleFonts.poppins(fontWeight: FontWeight.w700))),
      body: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(children: [
          Text('Step 3 — Questions', style: GoogleFonts.poppins(fontSize: 20, fontWeight: FontWeight.w700)),
          SizedBox(height: 12),
          Expanded(child: ListView.separated(
            separatorBuilder: (_,__) => SizedBox(height: 10),
            itemCount: questions.length,
            itemBuilder: (c,i) {
              final q = questions[i];
              return Card(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                elevation: 6,
                child: ListTile(
                  title: Text('Q${i+1}. ${q['question']}', style: TextStyle(fontWeight: FontWeight.w700)),
                  subtitle: Text('Keywords: ${(q['keywords'] ?? []).join(', ')}'),
                ),
              );
            },
          )),
          PrimaryButton(text: 'Start Interview', onPressed: () {
            Navigator.pushNamed(context, '/interview', arguments: {'session_id': sessionId, 'questions': questions});
          }),
        ]),
      ),
    );
  }
}
"@
Set-Content -Path .\lib\screens\question_list_screen.dart -Value $question_list -Encoding UTF8

# screens: interview_screen.dart (full Duolingo-style UI incl. animated progress & badges)
$interview_screen = @"
import 'package:flutter/material.dart';
import 'package:record/record.dart';
import 'package:google_fonts/google_fonts.dart';
import '../api/sessions_api.dart';
import '../widgets/primary_button.dart';
import '../widgets/duo_avatar.dart';

class InterviewScreen extends StatefulWidget {
  const InterviewScreen({Key? key}) : super(key: key);

  @override
  State<InterviewScreen> createState() => _InterviewScreenState();
}

class _InterviewScreenState extends State<InterviewScreen> with SingleTickerProviderStateMixin {
  late List<dynamic> questions;
  late int sessionId;
  int idx = 0;
  bool recording = false;
  final rec = Record();
  bool saving = false;

  late AnimationController _pulse;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(vsync: this, duration: Duration(milliseconds: 900));
    _pulse.repeat(reverse: true);
  }

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  Future<void> startStopRecording() async {
    if (!recording) {
      bool ok = await rec.hasPermission();
      if (!ok) { ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Microphone permission required'))); return; }
      final path = '/${DateTime.now().millisecondsSinceEpoch}.m4a';
      await rec.start(path: path, encoder: AudioEncoder.aacLc, bitRate: 128000);
      setState(() => recording = true);
    } else {
      final p = await rec.stop();
      setState(() => recording = false);
      // Placeholder transcript - we will add STT later
      await saveAndNext('Spoken answer placeholder (no STT). File: \$p');
    }
  }

  Future<void> saveAndNext(String transcript) async {
    setState(() => saving = true);
    try {
      await SessionsApi.saveAnswer(sessionId, questions[idx]['question'], transcript);
      if (idx < questions.length - 1) {
        setState(() => idx++);
      } else {
        final result = await SessionsApi.evaluateAll(sessionId);
        Navigator.pushNamed(context, '/results', arguments: result);
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Save failed: \$e')));
    } finally { setState(() => saving = false); }
  }

  @override
  Widget build(BuildContext context) {
    final args = ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
    sessionId = args['session_id'];
    questions = args['questions'];

    final total = questions.length;
    final current = questions[idx]['question'] ?? '';

    return Scaffold(
      body: Container(
        decoration: BoxDecoration(gradient: LinearGradient(colors: [Color(0xFF8359FF), Color(0xFFFF5EAB)], begin: Alignment.topLeft, end: Alignment.bottomRight)),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(18.0),
            child: Column(children: [
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                DuoAvatar(size: 58),
                Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
                  Text('Question ${idx+1}/$total', style: GoogleFonts.poppins(color: Colors.white, fontWeight: FontWeight.w700)),
                  SizedBox(height: 6),
                  LinearProgressIndicator(value: (idx+1)/total, backgroundColor: Colors.white24, color: Colors.white, minHeight: 8),
                ])
              ]),
              SizedBox(height: 18),
              Expanded(
                child: Container(
                  width: double.infinity,
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(22)),
                  padding: EdgeInsets.all(18),
                  child: Column(children: [
                    Text('Answer confidently', style: GoogleFonts.poppins(fontWeight: FontWeight.w700)),
                    SizedBox(height: 12),
                    Expanded(child: SingleChildScrollView(child: Text(current, style: GoogleFonts.inter(fontSize: 18)))),
                    SizedBox(height: 12),
                    Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                      Column(children: [
                        Icon(Icons.mic, size: 30, color: Color(0xFF8359FF)),
                        SizedBox(height: 6),
                        Text('Speak', style: GoogleFonts.inter(fontSize: 12))
                      ]),
                      ScaleTransition(
                        scale: Tween(begin: 1.0, end: 1.06).animate(CurvedAnimation(parent: _pulse, curve: Curves.easeInOut)),
                        child: PrimaryButton(
                          text: recording ? 'Stop & Save' : 'Start Recording',
                          loading: saving,
                          onPressed: startStopRecording,
                        ),
                      ),
                      Column(children: [
                        Icon(Icons.timer, size: 30, color: Color(0xFFFF5EAB)),
                        SizedBox(height: 6),
                        Text('Timed', style: GoogleFonts.inter(fontSize: 12))
                      ]),
                    ])
                  ]),
                ),
              ),
              SizedBox(height: 12),
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                TextButton(onPressed: () {
                  if (idx>0) setState(() => idx--);
                }, child: Text('Back', style: TextStyle(color: Colors.white))),
                Text('Tip: Keep answers concise', style: TextStyle(color: Colors.white70)),
                TextButton(onPressed: () async {
                  // Skip to evaluate (for demo)
                  final result = await SessionsApi.evaluateAll(sessionId);
                  Navigator.pushNamed(context, '/results', arguments: result);
                }, child: Text('Finish', style: TextStyle(color: Colors.white)))
              ])
            ]),
          ),
        ),
      ),
    );
  }
}
"@
Set-Content -Path .\lib\screens\interview_screen.dart -Value $interview_screen -Encoding UTF8

# screens: results_screen.dart (Polished badges and star animation)
$results_screen = @"
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../widgets/duo_avatar.dart';

class ResultsScreen extends StatelessWidget {
  const ResultsScreen({Key? key}) : super(key: key);

  Widget _badge(double score) {
    final int stars = (score / 20).clamp(0,5).toInt();
    return Row(children: List.generate(5, (i) => Icon(i < stars ? Icons.star : Icons.star_border, color: Colors.amber)));
  }

  @override
  Widget build(BuildContext context) {
    final result = ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
    final evaluations = List<dynamic>.from(result['evaluations'] ?? []);
    double overall = 0;
    if (evaluations.isNotEmpty) {
      overall = evaluations.map((e) => (e['score'] ?? 0)).fold(0.0, (a,b) => a + (b as num)) / evaluations.length;
    }

    return Scaffold(
      body: Container(
        decoration: BoxDecoration(gradient: LinearGradient(colors: [Color(0xFF8359FF), Color(0xFFFF5EAB)], begin: Alignment.topLeft, end: Alignment.bottomRight)),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(18.0),
            child: Column(children: [
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [DuoAvatar(size: 58), SizedBox(width:12), Text('Results', style: GoogleFonts.poppins(color: Colors.white, fontWeight: FontWeight.w800))]),
              SizedBox(height: 18),
              Card(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                elevation: 8,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(children: [
                    Text('Final Score', style: GoogleFonts.poppins(fontSize: 18, fontWeight: FontWeight.w700)),
                    SizedBox(height: 8),
                    Text('\${overall.toStringAsFixed(1)}/100', style: GoogleFonts.poppins(fontSize: 36, fontWeight: FontWeight.w800)),
                    SizedBox(height: 8),
                    _badge(overall),
                    SizedBox(height: 6),
                    Text('Strengths & Suggestions', style: GoogleFonts.inter(color: Colors.grey[700])),
                  ]),
                ),
              ),
              SizedBox(height: 12),
              Expanded(
                child: ListView.builder(
                  itemCount: evaluations.length,
                  itemBuilder: (c,i) {
                    final e = evaluations[i];
                    return Card(
                      margin: EdgeInsets.only(bottom: 10),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      child: ListTile(
                        title: Text(e['question'] ?? '', style: GoogleFonts.poppins(fontWeight: FontWeight.w700)),
                        subtitle: Text('Score: \${e['score'] ?? 'N/A'}\\nFeedback: \${(e['details']?['feedback']) ?? e['details'] ?? 'No feedback'}'),
                      ),
                    );
                  },
                ),
              ),
              PrimaryButton(text: 'Back to Home', onPressed: () {
                Navigator.pushNamedAndRemoveUntil(context, '/resume', (r) => false);
              }, loading: false)
            ]),
          ),
        ),
      ),
    );
  }
}
"@
Set-Content -Path .\lib\screens\results_screen.dart -Value $results_screen -Encoding UTF8

# main.dart
$main = @"
import 'package:flutter/material.dart';
import 'screens/splash_screen.dart';
import 'screens/resume_upload_screen.dart';
import 'screens/domain_select_screen.dart';
import 'screens/question_list_screen.dart';
import 'screens/interview_screen.dart';
import 'screens/results_screen.dart';

void main() {
  runApp(const InterviewApp());
}

class InterviewApp extends StatelessWidget {
  const InterviewApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Interview Coach',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(useMaterial3: true, colorScheme: ColorScheme.fromSeed(seedColor: Color(0xFF8359FF))),
      initialRoute: '/',
      routes: {
        '/': (c) => const SplashScreen(),
        '/resume': (c) => const ResumeUploadScreen(),
        '/domain_select': (c) => const DomainSelectScreen(),
        '/question_list': (c) => const QuestionListScreen(),
        '/interview': (c) => const InterviewScreen(),
        '/results': (c) => const ResultsScreen(),
      },
    );
  }
}
"@
Set-Content -Path .\lib\main.dart -Value $main -Encoding UTF8

Write-Host "All files created. Please update lib/api/api_client.dart with your backend IP (http://YOUR_IP:8000/api)."
Write-Host "Run: flutter pub get  && flutter run"
