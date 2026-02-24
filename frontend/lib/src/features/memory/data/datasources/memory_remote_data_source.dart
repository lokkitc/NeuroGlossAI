import '../../../../core/network/api_client.dart';

class MemoryRemoteDataSource {
  MemoryRemoteDataSource(this._client);

  final ApiClient _client;

  Future<List<Map<String, dynamic>>> listMy({int skip = 0, int limit = 100}) async {
    final list = await _client.getList('/memory/me', query: {'skip': skip, 'limit': limit});
    return list.map((e) => Map<String, dynamic>.from(e as Map)).toList(growable: false);
  }

  Future<Map<String, dynamic>> create(Map<String, dynamic> payload) => _client.postMap('/memory/me', data: payload);

  Future<Map<String, dynamic>> update(String id, Map<String, dynamic> payload) => _client.patchMap('/memory/me/$id', data: payload);

  Future<void> delete(String id) async {
    await _client.deleteMap('/memory/me/$id');
  }
}
