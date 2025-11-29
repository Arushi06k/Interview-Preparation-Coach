import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:google_fonts/google_fonts.dart';
import '../utils/report_exporter.dart';

class AnalysisScreen extends StatefulWidget {
  const AnalysisScreen({super.key});

  @override
  State<AnalysisScreen> createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen> {
  final GlobalKey repaintKey = GlobalKey();

  bool exporting = false;

  Future<void> _onExportPdf(Map<String, dynamic> result) async {
    setState(() => exporting = true);
    try {
      await ReportExporter.generateAndSharePdf(context, result);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('PDF export failed: $e')));
    } finally {
      setState(() => exporting = false);
    }
  }

  Future<void> _onExportImage() async {
    setState(() => exporting = true);
    try {
      await ReportExporter.captureAndShareImage(repaintKey);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Image export failed: $e')));
    } finally {
      setState(() => exporting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final result = ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
    final evaluations = List<dynamic>.from(result['evaluations'] ?? []);
    final scores = evaluations.map((e) => ((e['score'] ?? 0) as num).toDouble()).toList();
    final questions = evaluations.map((e) => (e['question'] ?? '').toString()).toList();
    final avg = scores.isEmpty ? 0.0 : scores.reduce((a, b) => a + b) / scores.length;

    int low = scores.where((s) => s <= 4).length;
    int med = scores.where((s) => s > 4 && s <= 7).length;
    int high = scores.where((s) => s > 7).length;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Detailed Analysis"),
        backgroundColor: const Color(0xFF4D9DE0),
        foregroundColor: Colors.white,
        actions: [
          // Download menu at top (you asked analysis top)
          PopupMenuButton<int>(
            onSelected: (v) async {
              if (v == 1) {
                await _onExportPdf(result);
              } else if (v == 2) {
                await _onExportImage();
              }
            },
            itemBuilder: (_) => [
              const PopupMenuItem(value: 1, child: Text('Download PDF')),
              const PopupMenuItem(value: 2, child: Text('Download Image (PNG)')),
            ],
            icon: exporting ? const Padding(
              padding: EdgeInsets.only(right: 12.0),
              child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)),
            ) : const Icon(Icons.download_rounded),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(18),
        child: RepaintBoundary(
          key: repaintKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // TITLE
              Text("Final Results & Feedback Report",
                  style: GoogleFonts.poppins(fontSize: 26, fontWeight: FontWeight.w800)),
              const SizedBox(height: 8),
              Text("Overall Average Score", style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w600)),
              Text("${(avg / 10).toStringAsFixed(1)} / 10",
                  style: GoogleFonts.poppins(fontSize: 32, fontWeight: FontWeight.w800, color: const Color(0xFF4D9DE0))),
              const SizedBox(height: 16),
              const Divider(),
              const SizedBox(height: 16),

              // SCORE CHART TITLE
              Text("Question-wise Score Chart", style: GoogleFonts.poppins(fontSize: 20, fontWeight: FontWeight.w700)),
              const SizedBox(height: 12),
              SizedBox(
                height: 350,
                child: BarChart(
                  BarChartData(
                    maxY: 10,
                    barGroups: List.generate(
                      scores.length,
                      (i) => BarChartGroupData(
                        x: i,
                        barRods: [
                          BarChartRodData(toY: scores[i], width: 14, color: const Color(0xFF4D9DE0)),
                        ],
                      ),
                    ),
                    titlesData: FlTitlesData(
                      leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: true)),
                      bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, getTitlesWidget: (v, meta) {
                        final idx = v.toInt();
                        if (idx < 0 || idx >= questions.length) return const SizedBox.shrink();
                        return Text(
                          questions[idx].length > 20 ? "${questions[idx].substring(0, 20)}…" : questions[idx],
                          style: const TextStyle(fontSize: 9),
                        );
                      })),
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 20),
              Text("Performance Distribution", style: GoogleFonts.poppins(fontSize: 20, fontWeight: FontWeight.w700)),
              const SizedBox(height: 12),
              SizedBox(
                height: 220,
                child: Row(
                  children: [
                    Expanded(
                      child: Column(children: [
                        Expanded(
                          child: Container(
                            color: Colors.transparent,
                            child: Center(
                              child: Text("${((low / (scores.isEmpty ? 1 : scores.length)) * 100).toStringAsFixed(0)}%\nLow (0-4)",
                                  textAlign: TextAlign.center, style: GoogleFonts.poppins(fontSize: 18)),
                            ),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Expanded(
                          child: Container(
                            color: Colors.transparent,
                            child: Center(
                              child: Text("${((med / (scores.isEmpty ? 1 : scores.length)) * 100).toStringAsFixed(0)}%\nMedium (5-7)",
                                  textAlign: TextAlign.center, style: GoogleFonts.poppins(fontSize: 18)),
                            ),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Expanded(
                          child: Container(
                            color: Colors.transparent,
                            child: Center(
                              child: Text("${((high / (scores.isEmpty ? 1 : scores.length)) * 100).toStringAsFixed(0)}%\nHigh (8-10)",
                                  textAlign: TextAlign.center, style: GoogleFonts.poppins(fontSize: 18)),
                            ),
                          ),
                        ),
                      ]),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Container(
                        decoration: BoxDecoration(borderRadius: BorderRadius.circular(10), color: Colors.white, boxShadow: const [
                          BoxShadow(color: Colors.black12, blurRadius: 8, offset: Offset(0, 4))
                        ]),
                        padding: const EdgeInsets.all(12),
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text("Weakest Questions (Needs Improvement)", style: GoogleFonts.poppins(fontSize: 16, fontWeight: FontWeight.w700)),
                          const SizedBox(height: 8),
                          ...evaluations.where((e) => (e['score'] ?? 0) <= 4).take(5).map((e) => Padding(
                                padding: const EdgeInsets.only(bottom: 8),
                                child: Text("• ${(e['question'] ?? '')}", style: GoogleFonts.inter()),
                              ))
                        ]),
                      ),
                    )
                  ],
                ),
              ),

              const SizedBox(height: 26),
              const Divider(),
              const SizedBox(height: 12),

              Text("Detailed Breakdown", style: GoogleFonts.poppins(fontSize: 20, fontWeight: FontWeight.w700)),
              const SizedBox(height: 12),

              Column(
                children: evaluations.map((e) {
                  return ExpansionTile(
                    title: Text("${e['question'] ?? ''} — Score: ${e['score']}/10", style: GoogleFonts.inter(fontWeight: FontWeight.w600)),
                    children: [
                      Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text("Your answer:", style: GoogleFonts.poppins(fontWeight: FontWeight.w700)),
                          const SizedBox(height: 6),
                          Text((e["your_answer"] ?? "No answer provided").toString(), style: GoogleFonts.inter(height: 1.4)),
                          const SizedBox(height: 14),
                          Text("Feedback:", style: GoogleFonts.poppins(fontWeight: FontWeight.w700)),
                          const SizedBox(height: 6),
                          Text((e["details"]?["feedback"] ?? e["details"] ?? "No feedback").toString(), style: GoogleFonts.inter(color: Colors.grey[700], height: 1.4)),
                        ]),
                      ),
                    ],
                  );
                }).toList(),
              ),

              const SizedBox(height: 26),
              const Divider(),
              const SizedBox(height: 16),

              Text("Personalized Improvement Plan", style: GoogleFonts.poppins(fontSize: 20, fontWeight: FontWeight.w700)),
              const SizedBox(height: 12),
              Text("📌 General\nStart from basics: watch short videos, read summaries, and practice 5–10 easy questions.", style: GoogleFonts.inter(fontSize: 15, height: 1.4)),

              const SizedBox(height: 40),

              // Final Start New Interview button is kept here (end of analysis)
              Center(
                child: ElevatedButton(
                  onPressed: () {
                    Navigator.pushNamedAndRemoveUntil(context, '/resume', (r) => false);
                  },
                  style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF4D9DE0), foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 30), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18))),
                  child: const Text("Start New Interview", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                ),
              ),

              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }
}
