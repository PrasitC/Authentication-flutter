import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class AuthService {
  static const String baseUrl = 'http://192.168.29.128:8000';
  
  // User model
  static Map<String, dynamic>? _currentUser;
  static String? _token;
  
  static Map<String, dynamic>? get currentUser => _currentUser;
  static String? get token => _token;
  static bool get isAuthenticated => _token != null;

  // Sign up
  static Future<Map<String, dynamic>> signUp({
    required String fullName,
    required String email,
    required String password,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/auth/signup'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'full_name': fullName,
          'email': email,
          'password': password,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _token = data['access_token'];
        _currentUser = data['user_info'];
        
        // Save to shared preferences
        await _saveToken(_token!);
        await _saveUser(_currentUser!);
        
        return {
          'success': true,
          'message': 'Account created successfully',
          'user': _currentUser,
        };
      } else {
        final errorData = jsonDecode(response.body);
        return {
          'success': false,
          'message': errorData['detail'] ?? 'Sign up failed',
        };
      }
    } catch (e) {
      return {
        'success': false,
        'message': 'Network error: ${e.toString()}',
      };
    }
  }

  // Sign in
  static Future<Map<String, dynamic>> signIn({
    required String email,
    required String password,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/auth/signin'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'email': email,
          'password': password,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _token = data['access_token'];
        _currentUser = data['user_info'];
        
        // Save to shared preferences
        await _saveToken(_token!);
        await _saveUser(_currentUser!);
        
        return {
          'success': true,
          'message': 'Signed in successfully',
          'user': _currentUser,
        };
      } else {
        final errorData = jsonDecode(response.body);
        return {
          'success': false,
          'message': errorData['detail'] ?? 'Sign in failed',
        };
      }
    } catch (e) {
      return {
        'success': false,
        'message': 'Network error: ${e.toString()}',
      };
    }
  }

  // Get items (protected route)
  static Future<Map<String, dynamic>> getItems() async {
    if (!isAuthenticated) {
      return {
        'success': false,
        'message': 'Not authenticated',
      };
    }

    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/items'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_token',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          'success': true,
          'items': data,
        };
      } else if (response.statusCode == 401) {
        // Token expired, sign out
        await signOut();
        return {
          'success': false,
          'message': 'Session expired, please sign in again',
        };
      } else {
        return {
          'success': false,
          'message': 'Failed to load items',
        };
      }
    } catch (e) {
      return {
        'success': false,
        'message': 'Network error: ${e.toString()}',
      };
    }
  }

  // Sign out
  static Future<void> signOut() async {
    _token = null;
    _currentUser = null;
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    await prefs.remove('user_info');
  }

  // Load saved authentication state
  static Future<void> loadAuthState() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString('auth_token');
    
    final userJson = prefs.getString('user_info');
    if (userJson != null) {
      _currentUser = jsonDecode(userJson);
    }
  }

  // Save token to shared preferences
  static Future<void> _saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('auth_token', token);
  }

  // Save user info to shared preferences
  static Future<void> _saveUser(Map<String, dynamic> user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('user_info', jsonEncode(user));
  }
}

// Item model
class Item {
  final int id;
  final String title;
  final String description;
  final String category;
  final DateTime createdAt;

  Item({
    required this.id,
    required this.title,
    required this.description,
    required this.category,
    required this.createdAt,
  });

  factory Item.fromJson(Map<String, dynamic> json) {
    return Item(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      category: json['category'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}