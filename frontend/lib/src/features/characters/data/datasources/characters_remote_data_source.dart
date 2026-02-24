import '../../../../core/network/api_client.dart';

class CharactersRemoteDataSource {
  CharactersRemoteDataSource(this._client);

  final ApiClient _client;

  Future<List<Map<String, dynamic>>> listMy({int skip = 0, int limit = 50}) async {
    final list = await _client.getList('/characters/me', query: {'skip': skip, 'limit': limit});
    return list.map((e) => Map<String, dynamic>.from(e as Map)).toList(growable: false);
  }

  Future<Map<String, dynamic>> create(Map<String, dynamic> payload) => _client.postMap('/characters/me', data: payload);

  Future<void> delete(String id) async {
    await _client.deleteMap('/characters/me/$id');
  }
}
