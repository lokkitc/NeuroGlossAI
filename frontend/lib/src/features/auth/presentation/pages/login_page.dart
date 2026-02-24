import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/widgets/app_button.dart';
import '../../../../core/widgets/app_text_field.dart';
import '../../../../core/widgets/async_view.dart';
import '../controllers/auth_controller.dart';

class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  final _username = TextEditingController();
  final _password = TextEditingController();

  @override
  void dispose() {
    _username.dispose();
    _password.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: AsyncView(
                value: auth,
                loading: () => const _LoginSkeleton(),
                errorBuilder: (message) => _LoginForm(
                  username: _username,
                  password: _password,
                  errorText: message,
                  isBusy: false,
                ),
                dataBuilder: (_) => _LoginForm(
                  username: _username,
                  password: _password,
                  errorText: null,
                  isBusy: auth.isLoading,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _LoginForm extends ConsumerWidget {
  const _LoginForm({
    required this.username,
    required this.password,
    required this.errorText,
    required this.isBusy,
  });

  final TextEditingController username;
  final TextEditingController password;
  final String? errorText;
  final bool isBusy;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Welcome back',
          style: Theme.of(context).textTheme.headlineMedium,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 8),
        Text(
          'Sign in to continue',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Theme.of(context).hintColor),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 24),
        if (errorText != null) ...[
          Text(errorText!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
          const SizedBox(height: 12),
        ],
        AppTextField(
          controller: username,
          labelText: 'Username',
          textInputAction: TextInputAction.next,
        ),
        const SizedBox(height: 12),
        AppTextField(
          controller: password,
          labelText: 'Password',
          obscureText: true,
          onSubmitted: (_) => _submit(ref),
        ),
        const SizedBox(height: 16),
        AppButton(
          text: isBusy ? 'Signing in...' : 'Sign in',
          onPressed: isBusy ? null : () => _submit(ref),
        ),
      ],
    );
  }

  void _submit(WidgetRef ref) {
    ref.read(authControllerProvider.notifier).login(
          username: username.text.trim(),
          password: password.text,
        );
  }
}

class _LoginSkeleton extends StatelessWidget {
  const _LoginSkeleton();

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: const [
        SizedBox(height: 24),
        _SkeletonLine(widthFactor: 0.6),
        SizedBox(height: 12),
        _SkeletonLine(widthFactor: 0.8),
        SizedBox(height: 24),
        _SkeletonBox(height: 56),
        SizedBox(height: 12),
        _SkeletonBox(height: 56),
        SizedBox(height: 16),
        _SkeletonBox(height: 52),
      ],
    );
  }
}

class _SkeletonLine extends StatelessWidget {
  const _SkeletonLine({required this.widthFactor});
  final double widthFactor;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.center,
      child: FractionallySizedBox(
        widthFactor: widthFactor,
        child: const _SkeletonBox(height: 18),
      ),
    );
  }
}

class _SkeletonBox extends StatelessWidget {
  const _SkeletonBox({required this.height});
  final double height;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(14),
      ),
    );
  }
}
