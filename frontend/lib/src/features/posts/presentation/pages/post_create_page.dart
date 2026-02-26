import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/widgets/app_button.dart';
import '../../../../core/widgets/app_text_field.dart';
import '../../domain/entities/post.dart';
import '../controllers/posts_controllers.dart';

class PostCreatePage extends ConsumerStatefulWidget {
  const PostCreatePage({super.key});

  @override
  ConsumerState<PostCreatePage> createState() => _PostCreatePageState();
}

class _PostCreatePageState extends ConsumerState<PostCreatePage> {
  final _title = TextEditingController();
  final _content = TextEditingController();

  bool _isPublic = true;
  bool _busy = false;
  String? _error;

  List<int>? _imageBytes;
  String? _imageFilename;

  @override
  void dispose() {
    _title.dispose();
    _content.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create post')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (_error != null) ...[
              Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
              const SizedBox(height: 12),
            ],
            AppTextField(controller: _title, labelText: 'Title'),
            const SizedBox(height: 12),
            AppTextField(controller: _content, labelText: 'Content'),
            const SizedBox(height: 12),
            SwitchListTile(
              value: _isPublic,
              onChanged: _busy ? null : (v) => setState(() => _isPublic = v),
              title: const Text('Public'),
              subtitle: const Text('Public posts can be liked'),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: Text(
                    _imageFilename ?? 'No image selected',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 8),
                OutlinedButton(
                  onPressed: _busy ? null : _pickImage,
                  child: const Text('Choose image'),
                ),
              ],
            ),
            const SizedBox(height: 16),
            AppButton(
              text: _busy ? 'Posting...' : 'Post',
              onPressed: _busy ? null : _submit,
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _pickImage() async {
    try {
      final res = await FilePicker.platform.pickFiles(type: FileType.image, withData: true);
      final f = res?.files.single;
      if (f == null) return;
      if (f.bytes == null) {
        setState(() => _error = 'Failed to read file bytes');
        return;
      }
      setState(() {
        _imageBytes = f.bytes!;
        _imageFilename = f.name;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }

  Future<void> _submit() async {
    setState(() {
      _busy = true;
      _error = null;
    });

    try {
      final media = <PostMediaEntity>[];
      if (_imageBytes != null && _imageFilename != null) {
        final json = await ref.read(uploadsRemoteDataSourceProvider).uploadImage(
              bytes: _imageBytes!,
              filename: _imageFilename!,
            );
        final url = (json['url'] as String?)?.trim() ?? '';
        if (url.isNotEmpty) {
          media.add(
            PostMediaEntity(
              url: url,
              publicId: json['public_id']?.toString(),
              width: json['width'] is int ? json['width'] as int : int.tryParse('${json['width']}'),
              height: json['height'] is int ? json['height'] as int : int.tryParse('${json['height']}'),
              bytes: json['bytes'] is int ? json['bytes'] as int : int.tryParse('${json['bytes']}'),
              format: json['format']?.toString(),
            ),
          );
        }
      }

      await ref.read(postsRepositoryProvider).create(
            title: _title.text.trim(),
            content: _content.text.trim(),
            isPublic: _isPublic,
            media: media.isEmpty ? null : media,
          );

      if (!mounted) return;
      ref.invalidate(publicPostsProvider);
      Navigator.of(context).pop();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }
}
