import 'package:dio/dio.dart';

class ApiService {
  // Remplace 127.0.0.1 par l'IP de ton serveur en production
  // Note : Sur l'émulateur Android, utilise 10.0.2.2 pour accéder au localhost de ton PC
  final String _baseUrl = "http://192.168.59.131/24:5000"; 
  
  final Dio _dio = Dio();

  ApiService() {
    _dio.options.baseUrl = _baseUrl;
    _dio.options.connectTimeout = const Duration(seconds: 10);
    _dio.options.receiveTimeout = const Duration(seconds: 10);
    _dio.options.headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
  }

  /// Vérifie le statut d'un utilisateur (Premium ou non)
  Future<Map<String, dynamic>> getUserStatus(String whatsappId) async {
    try {
      final response = await _dio.post('/webhook', data: {
        'message': 'CHECK_STATUS', // Commande interne pour le bot
        'sender': whatsappId,
      });

      if (response.statusCode == 200) {
        return {
          'success': true,
          'is_premium': response.data['is_premium'] ?? false,
          'user_name': response.data['user'] ?? 'Utilisateur',
        };
      }
      return {'success': false, 'error': 'Erreur serveur'};
    } on DioException catch (e) {
      return {'success': false, 'error': e.message};
    }
  }

  /// Génère un lien de paiement pour un abonnement
  Future<Map<String, dynamic>> initiatePayment(String whatsappId, String planType) async {
    try {
      // On peut imaginer une route /api/pay dédiée sur Flask
      final response = await _dio.post('/webhook', data: {
        'message': '/pay $planType', 
        'sender': whatsappId,
      });

      if (response.statusCode == 200) {
        return {
          'success': true,
          'payment_url': response.data['payment_url'],
          'transaction_id': response.data['transaction_id'],
        };
      }
      return {'success': false, 'error': 'Impossible de générer le lien'};
    } on DioException catch (e) {
      return {'success': false, 'error': e.message};
    }
  }
}

