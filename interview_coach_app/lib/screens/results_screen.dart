import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class ResultsScreen extends StatelessWidget {
  const ResultsScreen({super.key});

  Widget _starRating(double score) {
    int filled = (score / 20).clamp(0, 5).toInt();
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(
        5,
        (i) => Icon(
          i < filled ? Icons.star : Icons.star_border,
          color: Colors.amber,
          size: 28,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final result =
        ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;

    final evaluations = List<dynamic>.from(result["evaluations"] ?? []);
    double averageScore = 0;

    if (evaluations.isNotEmpty) {
      averageScore = evaluations
              .map((e) => (e["score"] ?? 0) as num)
              .fold(0.0, (a, b) => a + b) /
          evaluations.length;
    }

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
                Text(
                  "Results Summary",
                  style: GoogleFonts.poppins(
                    fontSize: 28,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 20),

                // MAIN CARD
                Card(
                  elevation: 8,
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(22)),
                  child: Padding(
                    padding: const EdgeInsets.all(22),
                    child: Column(
                      children: [
                        Text("Overall Score",
                            style: GoogleFonts.poppins(
                                fontSize: 18, fontWeight: FontWeight.w600)),
                        const SizedBox(height: 6),
                        Text(
                          "${averageScore.toStringAsFixed(1)} / 100",
                          style: GoogleFonts.poppins(
                            fontSize: 36,
                            fontWeight: FontWeight.w800,
                            color: const Color(0xFF4D9DE0),
                          ),
                        ),
                        const SizedBox(height: 10),
                        _starRating(averageScore),
                        const SizedBox(height: 14),
                        const Divider(),
                        const SizedBox(height: 14),
                        Text(
                          "Tap below to view full analysis including charts, strengths, weaknesses, and improvement plan.",
                          textAlign: TextAlign.center,
                          style: GoogleFonts.inter(
                              fontSize: 14, color: Colors.grey[700]),
                        ),
                      ],
                    ),
                  ),
                ),

                const Spacer(),

                // VIEW REPORT BUTTON
                ElevatedButton(
                  onPressed: () {
                    Navigator.pushNamed(context, "/analysis",
                        arguments: result);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: const Color(0xFF4D9DE0),
                    padding: const EdgeInsets.symmetric(
                        vertical: 14, horizontal: 28),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(18)),
                  ),
                  child: const Text(
                    "View Full Report",
                    style: TextStyle(
                        fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
