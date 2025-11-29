import 'package:flutter/material.dart';
import 'screens/splash_screen.dart';
import 'screens/resume_upload_screen.dart';
import 'screens/domain_select_screen.dart';
import 'screens/permissions_instructions_screen.dart';
import 'screens/question_list_screen.dart';
import 'screens/interview_screen.dart';
import 'screens/review_answers_screen.dart';
import 'screens/results_screen.dart';
import 'screens/analysis_screen.dart';

void main() {
  runApp(const InterviewApp());
}

class InterviewApp extends StatelessWidget {
  const InterviewApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Interview Coach',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
      useMaterial3: false, // keeps consistent render across platforms
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF4D9DE0),
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 24),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(18),
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: const Color(0xFF4D9DE0),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: const Color(0xFF4D9DE0),
          side: const BorderSide(color: Color(0xFF4D9DE0), width: 2),
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 24),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(18),
          ),
        ),
      ),
    ),

      initialRoute: '/',
      routes: {
        '/': (c) => const SplashScreen(),
        '/resume': (c) => const ResumeUploadScreen(),
        '/domain_select': (c) => const DomainSelectScreen(),
        '/permissions': (c) => const PermissionsInstructionsScreen(),
        '/question_list': (c) => const QuestionListScreen(),
        '/interview': (c) => const InterviewScreen(),
        '/review': (c) => const ReviewAnswersScreen(),
        '/results': (c) => const ResultsScreen(),
        '/analysis': (c) => const AnalysisScreen(),
      },
    );
  }
}
