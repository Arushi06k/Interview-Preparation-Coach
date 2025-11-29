// lib/api/sessions_api.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

/// Basic API wrapper for connecting to your FastAPI backend.
/// Update `baseUrl` if your backend runs on a different host/port.
class SessionsApi {
  // NOTE: change this to your backend address if needed
  // e.g. "http://10.149.243.53:8000" or "http://127.0.0.1:8000" for local
  static String baseUrl = "http://127.0.0.1:8080";

  static Uri _uri(String path) => Uri.parse("$baseUrl$path");

  /// create a new session (optional - your flow may create session elsewhere)
  static Future<Map<String, dynamic>> createSession(Map<String, dynamic> payload) async {
    final res = await http.post(_uri("/api/sessions"), headers: _jsonHeaders, body: jsonEncode(payload));
    _checkResponse(res);
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// generate questions for a session (if you need to call from FE)
  static Future<Map<String, dynamic>> generateQuestions(int sessionId) async {
    final res = await http.post(_uri("/api/sessions/$sessionId/generate-questions"));
    _checkResponse(res);
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Save a single raw answer to backend: payload = {"question":..., "answer":...}
  static Future<Map<String, dynamic>> saveAnswer(int sessionId, String question, String answer) async {
    final payload = {"question": question, "answer": answer};
    final res = await http.post(_uri("/api/sessions/$sessionId/save-answer"),
        headers: _jsonHeaders, body: jsonEncode(payload));
    _checkResponse(res);
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Evaluate all raw answers in session (bulk evaluation)
  static Future<Map<String, dynamic>> evaluateAll(int sessionId) async {
    final res = await http.post(_uri("/api/sessions/$sessionId/evaluate-all"));
    _checkResponse(res);
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Fetch final results for session
  static Future<Map<String, dynamic>> getResults(int sessionId) async {
    final res = await http.get(_uri("/api/sessions/$sessionId/results"));
    _checkResponse(res);
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Helper - minimal response check
  static void _checkResponse(http.Response res) {
    if (res.statusCode < 200 || res.statusCode >= 300) {
      String msg = "HTTP ${res.statusCode}";
      try {
        final body = jsonDecode(res.body);
        if (body is Map && body.containsKey("detail")) msg = body["detail"].toString();
      } catch (_) {}
      throw Exception("API error: $msg");
    }
  }

  static Map<String, String> get _jsonHeaders => {"Content-Type": "application/json"};
}
