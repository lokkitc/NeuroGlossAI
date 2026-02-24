import '../../../../core/network/api_client.dart';

class ChatRemoteDataSource {
  ChatRemoteDataSource(this._client);

  final ApiClient _client;

  Future<List<Map<String, dynamic>>> listSessions({int skip = 0, int limit = 50}) async {
    final list = await _client.getList('/chat/sessions', query: {'skip': skip, 'limit': limit});
    return list.map((e) => Map<String, dynamic>.from(e as Map)).toList(growable: false);
  }

  Future<Map<String, dynamic>> createSession(Map<String, dynamic> payload) => _client.postMap('/chat/sessions', data: payload);

  Future<Map<String, dynamic>> getSession(String sessionId) => _client.getMap('/chat/sessions/$sessionId');

  Future<Map<String, dynamic>> sendTurn(String sessionId, String content) => _client.postMap('/chat/sessions/$sessionId/turn', data: {'content': content});
}
