import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../errors/app_exception.dart';

class AsyncView<T> extends StatelessWidget {
  const AsyncView({
    super.key,
    required this.value,
    required this.dataBuilder,
    required this.errorBuilder,
    required this.loading,
  });

  final AsyncValue<T> value;
  final Widget Function(T data) dataBuilder;
  final Widget Function(String message) errorBuilder;
  final Widget Function() loading;

  @override
  Widget build(BuildContext context) {
    return value.when(
      data: dataBuilder,
      loading: loading,
      error: (err, _) {
        final msg = err is AppException ? err.message : err.toString();
        return errorBuilder(msg);
      },
    );
  }
}
