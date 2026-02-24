import 'package:flutter/material.dart';

class AnimatedListItem extends StatefulWidget {
  const AnimatedListItem({
    super.key,
    required this.index,
    required this.child,
    this.baseDelay = const Duration(milliseconds: 40),
    this.duration = const Duration(milliseconds: 260),
  });

  final int index;
  final Widget child;
  final Duration baseDelay;
  final Duration duration;

  @override
  State<AnimatedListItem> createState() => _AnimatedListItemState();
}

class _AnimatedListItemState extends State<AnimatedListItem> with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _t;
  bool _started = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: widget.duration);
    _t = CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic);
    _start();
  }

  Future<void> _start() async {
    final delay = Duration(milliseconds: widget.baseDelay.inMilliseconds * (widget.index.clamp(0, 12)));
    await Future<void>.delayed(delay);
    if (!mounted) return;
    _started = true;
    await _controller.forward();
  }

  @override
  void didUpdateWidget(covariant AnimatedListItem oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!_started) return;
    if (oldWidget.child.key != widget.child.key) {
      _controller.reset();
      _controller.forward();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _t,
      child: widget.child,
      builder: (context, child) {
        final v = _t.value;
        return Transform.translate(
          offset: Offset(0, (1 - v) * 10),
          child: Opacity(opacity: v, child: child),
        );
      },
    );
  }
}
