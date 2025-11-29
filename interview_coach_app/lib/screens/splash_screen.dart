import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});
  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> with SingleTickerProviderStateMixin {
  late AnimationController scale;

  @override
  void initState() {
    super.initState();
    scale = AnimationController(vsync: this, duration: const Duration(milliseconds: 900))..forward();
    Future.delayed(const Duration(milliseconds: 1200), () {
      Navigator.pushReplacementNamed(context, '/resume');
    });
  }

  @override
  void dispose() {
    scale.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(colors: [Color(0xFF4D9DE0), Color(0xFF87CEFA)], begin: Alignment.topLeft, end: Alignment.bottomRight),
        ),
        child: Center(
          child: ScaleTransition(
            scale: CurvedAnimation(curve: Curves.easeOutBack, parent: scale),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Container(
                height: 110,
                width: 110,
                decoration: BoxDecoration(borderRadius: BorderRadius.circular(28), color: Colors.white, boxShadow: const [BoxShadow(blurRadius: 18, offset: Offset(0,6), color: Colors.black26)]),
                child: const Center(child: Text("🤖", style: TextStyle(fontSize: 55))),
              ),
              const SizedBox(height: 22),
              Text("Interview Coach", style: GoogleFonts.poppins(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w800)),
              const SizedBox(height: 6),
              Text("AI-powered interview practice", style: GoogleFonts.inter(color: Colors.white70, fontSize: 14)),
            ]),
          ),
        ),
      ),
    );
  }
}
