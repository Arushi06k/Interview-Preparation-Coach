import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:google_fonts/google_fonts.dart';
import '../api/resume_api.dart';
import '../models/domain.dart';

class ResumeUploadScreen extends StatefulWidget {
  const ResumeUploadScreen({super.key});
  @override
  State<ResumeUploadScreen> createState() => _ResumeUploadScreenState();
}

class _ResumeUploadScreenState extends State<ResumeUploadScreen> {
  File? selectedFile;
  bool loading = false;

  Future<void> pickFile() async {
    final res = await FilePicker.platform.pickFiles(type: FileType.custom, allowedExtensions: ['pdf','docx']);
    if (res != null) setState(() => selectedFile = File(res.files.single.path!));
  }

  Future<void> upload() async {
    if (selectedFile == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please select a resume.")));
      return;
    }
    setState(() => loading = true);
    try {
      final result = await ResumeApi.uploadResume(selectedFile!);
      final domainModel = DomainModel.fromMap(result);
      Navigator.pushNamed(context, "/domain_select", arguments: domainModel);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Upload failed: $e")));
    }
    setState(() => loading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(gradient: LinearGradient(colors: [Color(0xFF4D9DE0), Color(0xFF87CEFA)], begin: Alignment.topLeft, end: Alignment.bottomRight)),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text("Step 1", style: GoogleFonts.poppins(fontSize: 16, color: Colors.white70)),
              const SizedBox(height: 4),
              Text("Upload your resume", style: GoogleFonts.poppins(fontSize: 26, fontWeight: FontWeight.w800, color: Colors.white)),
              const SizedBox(height: 20),
              Expanded(
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(22), boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 12, offset: Offset(0,6))]),
                  child: Column(children: [
                    const SizedBox(height: 30),
                    const Icon(Icons.upload_file, size: 70, color: Color(0xFF4D9DE0)),
                    const SizedBox(height: 12),
                    Text(selectedFile == null ? "No file selected" : selectedFile!.path.split("/").last, style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 18),
                    ElevatedButton(onPressed: pickFile, style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF4D9DE0), foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))), child: const Text("Pick PDF or DOCX")),
                    const Spacer(),
                    ElevatedButton(onPressed: loading ? null : upload, style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20), backgroundColor: const Color(0xFF4D9DE0), foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18))), child: loading ? const CircularProgressIndicator(color: Colors.white, strokeWidth: 2) : const Text("Upload & Continue", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold))),
                    const SizedBox(height: 10),
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
