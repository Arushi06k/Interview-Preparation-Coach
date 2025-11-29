// lib/utils/report_exporter.dart
import 'dart:io';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:path_provider/path_provider.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:share_plus/share_plus.dart';
import 'package:open_filex/open_filex.dart';

class ReportExporter {
  /// EXPORT PDF: build, save, open, and try to share.
  static Future<void> generateAndSharePdf(
      BuildContext context, Map<String, dynamic> result) async {
    final scaffold = ScaffoldMessenger.of(context);

    try {
      // Build PDF
      final pdf = pw.Document();

      final evaluations = List<dynamic>.from(result['evaluations'] ?? []);
      final scores = evaluations
          .map((e) => ((e['score'] ?? 0) as num).toDouble())
          .toList();
      final avg = scores.isEmpty ? 0.0 : scores.reduce((a, b) => a + b) / scores.length;

      // Try to load fallback fonts (if present in assets). If you have added NotoSans in assets/fonts, you can use them:
      pw.Font? fontRegular;
      pw.Font? fontBold;
      try {
        fontRegular = pw.Font.ttf(await rootBundle.load('assets/fonts/NotoSans-Regular.ttf'));
        fontBold = pw.Font.ttf(await rootBundle.load('assets/fonts/NotoSans-Bold.ttf'));
      } catch (_) {
        // fallback to built-in fonts
        fontRegular = pw.Font.helvetica();
        fontBold = pw.Font.helveticaBold();
      }

      pdf.addPage(
        pw.MultiPage(
          pageFormat: PdfPageFormat.a4,
          margin: const pw.EdgeInsets.symmetric(horizontal: 20, vertical: 32),
          theme: pw.ThemeData(defaultTextStyle: pw.TextStyle(font: fontRegular)),
          build: (context) => [
            pw.Text(
              "Interview Analysis Report",
              style: pw.TextStyle(font: fontBold, fontSize: 26, color: const PdfColor.fromInt(0xFF4D9DE0)),
            ),
            pw.SizedBox(height: 10),
            pw.Text("Overall Score", style: pw.TextStyle(font: fontBold, fontSize: 18)),
            pw.Text("${avg.toStringAsFixed(1)} / 10", style: pw.TextStyle(font: fontBold, fontSize: 30, color: const PdfColor.fromInt(0xFF4D9DE0))),
            pw.SizedBox(height: 20),
            pw.Divider(),
            pw.SizedBox(height: 20),
            pw.Text("Question-wise Scores", style: pw.TextStyle(font: fontBold, fontSize: 18)),
            pw.SizedBox(height: 12),
            pw.Column(
              crossAxisAlignment: pw.CrossAxisAlignment.start,
              children: evaluations.map((e) {
                final q = e['question'] ?? "";
                final sc = ((e['score'] ?? 0) as num).toDouble();
                return pw.Padding(
                  padding: const pw.EdgeInsets.only(bottom: 12),
                  child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
                    pw.Text(q.toString(), style: pw.TextStyle(font: fontBold, fontSize: 12)),
                    pw.SizedBox(height: 4),
                    pw.Container(height: 8, width: (sc / 10) * 300, color: const PdfColor.fromInt(0xFF4D9DE0)),
                    pw.SizedBox(height: 4),
                    pw.Text("${sc.toStringAsFixed(1)} / 10", style: const pw.TextStyle(fontSize: 10)),
                  ]),
                );
              }).toList(),
            ),
            pw.SizedBox(height: 20),
            pw.Divider(),
            pw.SizedBox(height: 20),
            pw.Text("Detailed Breakdown", style: pw.TextStyle(font: fontBold, fontSize: 18)),
            pw.SizedBox(height: 10),
            ...evaluations.map((e) {
              return pw.Container(
                padding: const pw.EdgeInsets.all(12),
                margin: const pw.EdgeInsets.only(bottom: 12),
                decoration: pw.BoxDecoration(
                  border: pw.Border.all(color: PdfColors.grey),
                  borderRadius: pw.BorderRadius.circular(6),
                ),
                child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
                  pw.Text(e['question']?.toString() ?? "", style: pw.TextStyle(font: fontBold, fontSize: 14)),
                  pw.SizedBox(height: 4),
                  pw.Text("Your answer:", style: pw.TextStyle(font: fontBold, fontSize: 12)),
                  pw.Text((e["your_answer"] ?? "No answer").toString(), style: const pw.TextStyle(fontSize: 11)),
                  pw.SizedBox(height: 6),
                  pw.Text("Feedback:", style: pw.TextStyle(font: fontBold, fontSize: 12)),
                  pw.Text((e["details"]?["feedback"] ?? e["details"] ?? "No feedback available").toString(), style: const pw.TextStyle(fontSize: 11)),
                ]),
              );
            }).toList(),
          ],
        ),
      );

      // Save file
      final bytes = await pdf.save();
      final tempDir = await getTemporaryDirectory();
      final file = File('${tempDir.path}/Interview_Report_${DateTime.now().millisecondsSinceEpoch}.pdf');
      await file.writeAsBytes(bytes);

      // Open with default app (reliable on desktop/mobile)
      await OpenFilex.open(file.path);

      // Try sharing as well (best-effort). share_plus may not open a file-share dialog on all desktop platforms.
      try {
        final xfile = XFile(file.path);
        // Use the high-level API. If deprecated warnings appear, still works on many platforms.
        await Share.shareXFiles([xfile], text: 'Interview Analysis Report (PDF)');
      } catch (_) {
        // ignore share errors, file already opened
      }

      scaffold.showSnackBar(SnackBar(content: Text('PDF saved and opened: ${file.path}')));
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('PDF export failed: $e')));
      rethrow;
    }
  }

  /// EXPORT ANALYSIS IMAGE: capture RepaintBoundary, save PNG, open and try share
  static Future<void> captureAndShareImage(GlobalKey repaintKey, {BuildContext? context}) async {
    final boundary = repaintKey.currentContext?.findRenderObject() as RenderRepaintBoundary?;
    if (boundary == null) {
      if (context != null) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Capture boundary not found')));
      }
      throw Exception('RepaintBoundary missing');
    }

    final ui.Image image = await boundary.toImage(pixelRatio: 2.5);
    final ByteData? byteData = await image.toByteData(format: ui.ImageByteFormat.png);
    if (byteData == null) {
      if (context != null) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Failed to encode image')));
      }
      throw Exception('Image encoding failed');
    }

    final pngBytes = byteData.buffer.asUint8List();
    final tempDir = await getTemporaryDirectory();
    final file = File('${tempDir.path}/Analysis_${DateTime.now().millisecondsSinceEpoch}.png');
    await file.writeAsBytes(pngBytes);

    // Open image with default app (works on desktop/mobile)
    await OpenFilex.open(file.path);

    // Try to share as well
    try {
      final xfile = XFile(file.path);
      await Share.shareXFiles([xfile], text: 'Interview Analysis Image');
    } catch (_) {
      // ignore share errors
    }
  }
}
