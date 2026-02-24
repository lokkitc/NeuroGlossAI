import 'package:flutter/material.dart';

class SkeletonList extends StatelessWidget {
  const SkeletonList({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemBuilder: (_, __) => Container(
        height: 68,
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(14),
        ),
      ),
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemCount: 8,
    );
  }
}
