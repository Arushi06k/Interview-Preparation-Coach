import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/domain.dart';

class DomainSelectScreen extends StatefulWidget {
  const DomainSelectScreen({super.key});
  @override
  State<DomainSelectScreen> createState() => _DomainSelectScreenState();
}

class _DomainSelectScreenState extends State<DomainSelectScreen> {
  String? selectedDomain;
  String selectedDifficulty = 'Medium';
  bool loading = false;

  @override
  Widget build(BuildContext context) {
    final domainModel = ModalRoute.of(context)!.settings.arguments as DomainModel;
    final domains = domainModel.topDomains;

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(gradient: LinearGradient(colors: [Color(0xFF4D9DE0), Color(0xFF87CEFA)], begin: Alignment.topLeft, end: Alignment.bottomRight)),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text("Step 2", style: GoogleFonts.poppins(fontSize: 16, color: Colors.white70)),
              const SizedBox(height: 4),
              Text("Choose your domain", style: GoogleFonts.poppins(fontSize: 26, fontWeight: FontWeight.w800, color: Colors.white)),
              const SizedBox(height: 20),
              Expanded(
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(22), boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 12, offset: Offset(0,6))]),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text("Detected from your resume:", style: GoogleFonts.poppins(fontSize: 18, fontWeight: FontWeight.w700)),
                    const SizedBox(height: 12),
                    Expanded(
                      child: ListView.separated(
                        itemCount: domains.length,
                        separatorBuilder: (_,__) => const SizedBox(height: 10),
                        itemBuilder: (context, index) {
                          final item = domains[index];
                          // Backend may return map or string; handle both
                          final d = (item is String) ? item : (item['domain_name'] ?? item.toString());
                          final isSelected = selectedDomain == d;
                          return GestureDetector(
                            onTap: () => setState(() => selectedDomain = d),
                            child: Container(
                              padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(14),
                                color: isSelected ? const Color(0xFF4D9DE0).withOpacity(0.12) : Colors.grey[100],
                                border: Border.all(color: isSelected ? const Color(0xFF4D9DE0) : Colors.transparent, width: 2),
                              ),
                              child: Row(children: [Expanded(child: Text(d.toString(), style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w600))), if (isSelected) const Icon(Icons.check_circle, color: Color(0xFF4D9DE0))]),
                            ),
                          );
                        },
                      ),
                    ),

                    const SizedBox(height: 12),

                    // Difficulty selector
                    Text("Choose difficulty", style: GoogleFonts.poppins(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 8),
                    Row(children: ['Easy','Medium','Hard'].map((lvl) {
                      final active = selectedDifficulty == lvl;
                      return Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: ChoiceChip(
                          label: Text(lvl),
                          selected: active,
                          onSelected: (_) => setState(() => selectedDifficulty = lvl),
                          selectedColor: const Color(0xFF4D9DE0),
                          backgroundColor: Colors.grey[100],
                          labelStyle: TextStyle(color: active ? Colors.white : Colors.black87, fontWeight: FontWeight.w600),
                        ),
                      );
                    }).toList()),

                    const SizedBox(height: 14),

                    ElevatedButton(
                      onPressed: loading ? null : () {
                        if (selectedDomain == null) {
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please select a domain")));
                          return;
                        }
                        final payload = {
                          'selected_domain': selectedDomain,
                          'difficulty_level': selectedDifficulty,
                          'resume_analysis_result': {'filename': domainModel.filename, 'top_domains': domainModel.topDomains}
                        };
                        // navigate to permission/instructions, pass payload
                        Navigator.pushNamed(context, '/permissions', arguments: payload);
                      },
                      style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF4D9DE0), foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18))),
                      child: const Text("Next: Setup", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
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
