import '../../../../core/network/api_client.dart';

class ChatLearningRemoteDataSource {
  ChatLearningRemoteDataSource(this._client);

  final ApiClient _client;

  Future<List<Map<String, dynamic>>> listLessons(String sessionId, {int skip = 0, int limit = 50}) async {
    final list = await _client.getList(
      '/chat-learning/sessions/$sessionId/learning/lessons',
      query: {'skip': skip, 'limit': limit},
    );
    return list.map((e) => Map<String, dynamic>.from(e as Map)).toList(growable: false);
  }

  Future<Map<String, dynamic>> generateLesson(String sessionId, {int turnWindow = 80, String generationMode = 'balanced'}) {
    return _client.postMap(
      '/chat-learning/sessions/$sessionId/learning/lessons',
      data: {'turn_window': turnWindow, 'generation_mode': generationMode},
    );
  }
}
