import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';

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

  List<int>? _avatarBytes;
  String? _avatarFilename;

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
                  const SizedBox(height: 12),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      'Avatar',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          _avatarFilename ?? 'No file selected',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 8),
                      OutlinedButton(
                        onPressed: _busy ? null : _pickAvatar,
                        child: const Text('Choose'),
                      ),
                    ],
                  ),
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
      String? avatarUrl;
      if (_avatarBytes != null && _avatarFilename != null) {
        final json = await ref.read(uploadsRemoteDataSourceProvider).uploadImage(
              bytes: _avatarBytes!,
              filename: _avatarFilename!,
            );
        avatarUrl = (json['url'] as String?)?.trim();
      }

      await ref.read(charactersRepositoryProvider).create(
            slug: _slug.text.trim(),
            displayName: _name.text.trim(),
            description: _desc.text.trim(),
            systemPrompt: _system.text,
            avatarUrl: avatarUrl,
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

  Future<void> _pickAvatar() async {
    try {
      final res = await FilePicker.platform.pickFiles(
        type: FileType.image,
        withData: true,
      );
      final f = res?.files.single;
      if (f == null) return;
      if (f.bytes == null) {
        setState(() => _error = 'Failed to read file bytes');
        return;
      }
      setState(() {
        _avatarBytes = f.bytes!;
        _avatarFilename = f.name;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }
}
