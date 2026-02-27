import '../../../../core/network/api_client.dart';

class PublicUsersRemoteDataSource {
  PublicUsersRemoteDataSource(this._client);

  final ApiClient _client;

  Future<List<Map<String, dynamic>>> listUsers({String? q, int skip = 0, int limit = 50}) async {
    final list = await _client.getList(
      '/public/users',
      query: {
        if (q != null && q.trim().isNotEmpty) 'q': q.trim(),
        'skip': skip,
        'limit': limit,
      },
    );

    return list
        .whereType<Map>()
        .map((e) => Map<String, dynamic>.from(e))
        .toList(growable: false);
  }

  Future<Map<String, dynamic>> getByUsername({required String username}) {
    return _client.getMap('/public/users/by-username/$username');
  }
}
