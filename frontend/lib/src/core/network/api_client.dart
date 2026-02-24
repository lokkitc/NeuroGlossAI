import 'package:dio/dio.dart';

import '../errors/error_mapper.dart';
import '../errors/app_exception.dart';

class ApiClient {
  ApiClient(this._dio);

  final Dio _dio;

  Future<Map<String, dynamic>> getMap(String path, {Map<String, dynamic>? query, Options? options}) async {
    try {
      final res = await _dio.get<dynamic>(path, queryParameters: query, options: options);
      final data = res.data;
      if (data is Map<String, dynamic>) return data;
      if (data is Map) return Map<String, dynamic>.from(data);
      throw Exception('Expected JSON object');
    } catch (e) {
      throw ErrorMapper.map(e);
    }
  }

  Future<Map<String, dynamic>> patchMap(String path, {Object? data, Map<String, dynamic>? query, Options? options}) async {
    try {
      final res = await _dio.patch<dynamic>(path, data: data, queryParameters: query, options: options);
      final body = res.data;
      if (body is Map<String, dynamic>) return body;
      if (body is Map) return Map<String, dynamic>.from(body);
      throw Exception('Expected JSON object');
    } catch (e) {
      throw ErrorMapper.map(e);
    }
  }

  Future<Map<String, dynamic>> deleteMap(String path, {Object? data, Map<String, dynamic>? query, Options? options}) async {
    try {
      final res = await _dio.delete<dynamic>(path, data: data, queryParameters: query, options: options);
      final body = res.data;
      if (body is Map<String, dynamic>) return body;
      if (body is Map) return Map<String, dynamic>.from(body);
      throw Exception('Expected JSON object');
    } catch (e) {
      throw ErrorMapper.map(e);
    }
  }

  Future<List<dynamic>> getList(String path, {Map<String, dynamic>? query, Options? options}) async {
    try {
      final res = await _dio.get<dynamic>(path, queryParameters: query, options: options);
      final data = res.data;
      if (data is List) return data;
      throw Exception('Expected JSON array');
    } catch (e) {
      throw ErrorMapper.map(e);
    }
  }

  Future<Map<String, dynamic>> postMap(String path, {Object? data, Map<String, dynamic>? query, Options? options}) async {
    try {
      final res = await _dio.post<dynamic>(path, data: data, queryParameters: query, options: options);
      final body = res.data;
      if (body is Map<String, dynamic>) return body;
      if (body is Map) return Map<String, dynamic>.from(body);
      throw Exception('Expected JSON object');
    } catch (e) {
      throw ErrorMapper.map(e);
    }
  }

  Future<List<dynamic>> postList(String path, {Object? data, Map<String, dynamic>? query, Options? options}) async {
    try {
      final res = await _dio.post<dynamic>(path, data: data, queryParameters: query, options: options);
      final body = res.data;
      if (body is List) return body;
      throw Exception('Expected JSON array');
    } catch (e) {
      throw ErrorMapper.map(e);
    }
  }

  Future<Map<String, dynamic>> postForm(
    String path, {
    required Map<String, dynamic> form,
    Map<String, dynamic>? query,
    Options? options,
  }) async {
    try {
      final res = await _dio.post<dynamic>(
        path,
        data: FormData.fromMap(form),
        queryParameters: query,
        options: options,
      );
      final data = res.data;
      if (data is Map<String, dynamic>) return data;
      if (data is Map) return Map<String, dynamic>.from(data);
      throw Exception('Expected JSON object');
    } catch (e) {
      final mapped = ErrorMapper.map(e);
      if (mapped is NetworkException && mapped.statusCode == 422) {
        // FastAPI can return 422 for invalid form.
        throw NetworkException('Invalid credentials', statusCode: 422);
      }
      throw mapped;
    }
  }
}
