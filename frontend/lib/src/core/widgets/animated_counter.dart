import 'package:flutter/material.dart';

class AnimatedCounter extends StatelessWidget {
  const AnimatedCounter({
    super.key,
    required this.value,
    this.duration = const Duration(milliseconds: 650),
    this.curve = Curves.easeOutCubic,
  });

  final int value;
  final Duration duration;
  final Curve curve;

  @override
  Widget build(BuildContext context) {
    final style = Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800);

    return TweenAnimationBuilder<int>(
      tween: IntTween(begin: 0, end: value),
      duration: duration,
      curve: curve,
      builder: (context, v, _) => Text('$v', style: style),
    );
  }
}
