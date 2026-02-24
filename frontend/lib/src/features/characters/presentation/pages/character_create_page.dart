import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/widgets/app_button.dart';
import '../../../../core/widgets/app_text_field.dart';
import '../../presentation/controllers/characters_controller.dart';

class CharacterCreatePage extends ConsumerStatefulWidget {
  const CharacterCreatePage({super.key});

  @override
  ConsumerState<CharacterCreatePage> createState() => _CharacterCreatePageState();
}

class _CharacterCreatePageState extends ConsumerState<CharacterCreatePage> {
  final _formKey = GlobalKey<FormState>();
  final _slug = TextEditingController();
  final _name = TextEditingController();
  final _system = TextEditingController(text: 'You are a helpful character.');
  final _desc = TextEditingController();

  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _slug.dispose();
    _name.dispose();
    _system.dispose();
    _desc.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create Character')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (_error != null) ...[
              Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
              const SizedBox(height: 12),
            ],
            Form(
              key: _formKey,
              child: Column(
                children: [
                  AppTextField(controller: _slug, labelText: 'Slug (unique)'),
                  const SizedBox(height: 12),
                  AppTextField(controller: _name, labelText: 'Display name'),
                  const SizedBox(height: 12),
                  AppTextField(controller: _desc, labelText: 'Description'),
                  const SizedBox(height: 12),
                  AppTextField(controller: _system, labelText: 'System prompt'),
                  const SizedBox(height: 16),
                  AppButton(text: _busy ? 'Creating...' : 'Create', onPressed: _busy ? null : _submit),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _submit() async {
    setState(() {
      _busy = true;
      _error = null;
    });

    try {
      await ref.read(charactersRepositoryProvider).create(
            slug: _slug.text.trim(),
            displayName: _name.text.trim(),
            description: _desc.text.trim(),
            systemPrompt: _system.text,
          );
      if (!mounted) return;
      ref.read(myCharactersProvider.notifier).refresh();
      Navigator.of(context).pop();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }
}
