import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/models.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = 'http://10.0.2.2:8000/api/v1'; // Default for emulator
  
  Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    // Using the mockup user id for demo purposes. In real app, this comes from Supabase Auth
    return prefs.getString('auth_token') ?? 'dev:11111111-1111-1111-1111-111111111111';
  }

  Future<Map<String, String>> _getHeaders() async {
    final token = await _getToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  Future<Map<String, dynamic>> getTodayHealth() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(Uri.parse('$baseUrl/health/today'), headers: headers);
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      print('Network error: $e');
    }
    return {'has_checked_in': false};
  }

  Future<Recommendation?> submitCheckIn(Map<String, dynamic> data) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('$baseUrl/checkin'),
        headers: headers,
        body: jsonEncode(data),
      );
      if (response.statusCode == 201) {
        return Recommendation.fromJson(jsonDecode(response.body));
      }
    } catch (e) {
      print('Network error: $e');
    }
    return null;
  }

  Future<bool> markComplete(String recId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('$baseUrl/recommendations/$recId/complete'),
        headers: headers,
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Network error: $e');
      return false;
    }
  }

  Future<bool> submitFeedback(String recId, String didComplete, String didHelp) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('$baseUrl/recommendations/$recId/feedback'),
        headers: headers,
        body: jsonEncode({'did_complete': didComplete, 'did_help': didHelp}),
      );
      return response.statusCode == 201;
    } catch (e) {
      print('Network error: $e');
      return false;
    }
  }

  Future<Map<String, dynamic>> getWeeklyInsights() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(Uri.parse('$baseUrl/insights/weekly'), headers: headers);
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      print('Network error: $e');
    }
    return {'has_sufficient_data': false, 'message': 'Network error'};
  }
}

final apiService = ApiService();
