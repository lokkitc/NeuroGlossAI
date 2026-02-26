import 'package:dio/dio.dart';

import 'api_client.dart';

class UploadsRemoteDataSource {
  UploadsRemoteDataSource(this._client);

  final ApiClient _client;

  Future<Map<String, dynamic>> uploadImage({required List<int> bytes, required String filename}) async {
    final form = FormData.fromMap({
      'image': MultipartFile.fromBytes(bytes, filename: filename),
    });
    return _client.postMultipartMap('/uploads/image', formData: form);
  }
}
