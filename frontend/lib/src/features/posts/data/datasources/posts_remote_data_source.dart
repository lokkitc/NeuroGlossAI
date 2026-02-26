import '../../../../core/network/api_client.dart';

class PostsRemoteDataSource {
  PostsRemoteDataSource(this._client);

  final ApiClient _client;

  Future<List<Map<String, dynamic>>> listPublic({int skip = 0, int limit = 50}) async {
    final list = await _client.getList('/posts/public', query: {'skip': skip, 'limit': limit});
    return list.map((e) => Map<String, dynamic>.from(e as Map)).toList(growable: false);
  }

  Future<List<Map<String, dynamic>>> listMine({int skip = 0, int limit = 50}) async {
    final list = await _client.getList('/posts/me', query: {'skip': skip, 'limit': limit});
    return list.map((e) => Map<String, dynamic>.from(e as Map)).toList(growable: false);
  }

  Future<Map<String, dynamic>> create(Map<String, dynamic> payload) => _client.postMap('/posts/me', data: payload);

  Future<void> delete(String id) async {
    await _client.deleteMap('/posts/me/$id');
  }

  Future<void> like(String id) async {
    await _client.postMap('/posts/$id/like');
  }

  Future<void> unlike(String id) async {
    await _client.deleteMap('/posts/$id/like');
  }
}
