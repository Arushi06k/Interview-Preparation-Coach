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
