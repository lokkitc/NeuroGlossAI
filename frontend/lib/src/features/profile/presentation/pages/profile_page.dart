import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'package:go_router/go_router.dart';

import '../../../auth/presentation/controllers/auth_controller.dart';
import '../../../../core/constants/routes.dart';
import '../../../../core/di/locator.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/uploads_remote_data_source.dart';
import '../../../posts/presentation/controllers/posts_controllers.dart';

final uploadsRemoteDataSourceProvider = Provider<UploadsRemoteDataSource>((ref) {
  return UploadsRemoteDataSource(sl<ApiClient>());
});

class ProfilePage extends ConsumerWidget {
  const ProfilePage({super.key});

  Future<String?> _pickAndUploadImage(BuildContext context, WidgetRef ref) async {
    final res = await FilePicker.platform.pickFiles(type: FileType.image, withData: true);
    final f = res?.files.single;
    if (f == null) return null;
    final bytes = f.bytes;
    if (bytes == null || bytes.isEmpty) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Failed to read file bytes')));
      }
      return null;
    }

    if (!context.mounted) return null;
    showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (_) => const Center(child: CircularProgressIndicator()),
    );

    try {
      final json = await ref.read(uploadsRemoteDataSourceProvider).uploadImage(bytes: bytes, filename: f.name);
      final url = (json['url'] as String?)?.trim();
      return (url == null || url.isEmpty) ? null : url;
    } finally {
      if (context.mounted) {
        Navigator.of(context, rootNavigator: true).pop();
      }
    }
  }

  Future<void> _changeAvatar(BuildContext context, WidgetRef ref) async {
    try {
      final url = await _pickAndUploadImage(context, ref);
      if (url == null) return;
      await ref.read(authControllerProvider.notifier).updateProfile(avatarUrl: url);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Avatar updated')));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  Future<void> _changeBanner(BuildContext context, WidgetRef ref) async {
    try {
      final url = await _pickAndUploadImage(context, ref);
      if (url == null) return;
      await ref.read(authControllerProvider.notifier).updateProfile(bannerUrl: url);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Banner updated')));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  Future<void> _showEditSheet(BuildContext context, WidgetRef ref) async {
    final auth = ref.read(authControllerProvider).valueOrNull;
    final user = auth?.user;
    if (user == null) return;

    final preferredNameCtrl = TextEditingController(text: user.preferredName ?? '');
    final bioCtrl = TextEditingController(text: user.bio ?? '');
    final timezoneCtrl = TextEditingController(text: user.timezone ?? 'UTC');
    final targetLangCtrl = TextEditingController(text: user.targetLanguage ?? '');
    final nativeLangCtrl = TextEditingController(text: user.nativeLanguage ?? '');
    final interestsCtrl = TextEditingController(text: (user.interests ?? const <String>[]).join(', '));
    final avatarCtrl = TextEditingController(text: user.avatarUrl ?? '');
    final bannerCtrl = TextEditingController(text: user.bannerUrl ?? '');
    String uiTheme = user.uiTheme ?? 'system';
    String assistantTone = user.assistantTone ?? 'friendly';
    final verbosityCtrl = TextEditingController(text: (user.assistantVerbosity ?? 3).toString());

    final formKey = GlobalKey<FormState>();

    final saved = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      useSafeArea: true,
      builder: (sheetContext) {
        final bottomInset = MediaQuery.of(sheetContext).viewInsets.bottom;
        return Padding(
          padding: EdgeInsets.only(bottom: bottomInset),
          child: DraggableScrollableSheet(
            expand: false,
            initialChildSize: 0.86,
            minChildSize: 0.5,
            maxChildSize: 0.95,
            builder: (context, scrollController) {
              return Form(
                key: formKey,
                child: ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            'Edit profile',
                            style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
                          ),
                        ),
                        IconButton(
                          onPressed: () => Navigator.of(sheetContext).pop(false),
                          icon: const Icon(Icons.close),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    _SectionCard(
                      title: 'Basics',
                      child: Column(
                        children: [
                          TextFormField(
                            controller: preferredNameCtrl,
                            decoration: const InputDecoration(
                              labelText: 'Preferred name',
                              prefixIcon: Icon(Icons.badge_outlined),
                            ),
                          ),
                          const SizedBox(height: 12),
                          TextFormField(
                            controller: bioCtrl,
                            decoration: const InputDecoration(
                              labelText: 'Bio',
                              prefixIcon: Icon(Icons.edit_note_outlined),
                            ),
                            minLines: 2,
                            maxLines: 5,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),
                    _SectionCard(
                      title: 'Languages',
                      child: Column(
                        children: [
                          TextFormField(
                            controller: nativeLangCtrl,
                            decoration: const InputDecoration(
                              labelText: 'Native language',
                              prefixIcon: Icon(Icons.language_outlined),
                            ),
                          ),
                          const SizedBox(height: 12),
                          TextFormField(
                            controller: targetLangCtrl,
                            decoration: const InputDecoration(
                              labelText: 'Target language',
                              prefixIcon: Icon(Icons.flag_outlined),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),
                    _SectionCard(
                      title: 'Personalization',
                      child: Column(
                        children: [
                          TextFormField(
                            controller: interestsCtrl,
                            decoration: const InputDecoration(
                              labelText: 'Interests (comma-separated)',
                              prefixIcon: Icon(Icons.local_offer_outlined),
                            ),
                          ),
                          const SizedBox(height: 12),
                          TextFormField(
                            controller: timezoneCtrl,
                            decoration: const InputDecoration(
                              labelText: 'Timezone',
                              prefixIcon: Icon(Icons.schedule_outlined),
                            ),
                          ),
                          const SizedBox(height: 12),
                          DropdownButtonFormField<String>(
                            value: uiTheme,
                            decoration: const InputDecoration(
                              labelText: 'UI theme',
                              prefixIcon: Icon(Icons.palette_outlined),
                            ),
                            items: const [
                              DropdownMenuItem(value: 'system', child: Text('System')),
                              DropdownMenuItem(value: 'light', child: Text('Light')),
                              DropdownMenuItem(value: 'dark', child: Text('Dark')),
                            ],
                            onChanged: (v) => uiTheme = v ?? 'system',
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),
                    _SectionCard(
                      title: 'Assistant',
                      child: Column(
                        children: [
                          DropdownButtonFormField<String>(
                            value: assistantTone,
                            decoration: const InputDecoration(
                              labelText: 'Tone',
                              prefixIcon: Icon(Icons.record_voice_over_outlined),
                            ),
                            items: const [
                              DropdownMenuItem(value: 'friendly', child: Text('Friendly')),
                              DropdownMenuItem(value: 'neutral', child: Text('Neutral')),
                              DropdownMenuItem(value: 'strict', child: Text('Strict')),
                            ],
                            onChanged: (v) => assistantTone = v ?? 'friendly',
                          ),
                          const SizedBox(height: 12),
                          TextFormField(
                            controller: verbosityCtrl,
                            decoration: const InputDecoration(
                              labelText: 'Verbosity (1-10)',
                              prefixIcon: Icon(Icons.tune_outlined),
                            ),
                            keyboardType: TextInputType.number,
                            validator: (v) {
                              final raw = (v ?? '').trim();
                              if (raw.isEmpty) return null;
                              final n = int.tryParse(raw);
                              if (n == null || n < 1 || n > 10) return 'Enter a number between 1 and 10';
                              return null;
                            },
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),
                    _SectionCard(
                      title: 'Images',
                      child: Column(
                        children: [
                          TextFormField(
                            controller: avatarCtrl,
                            decoration: const InputDecoration(
                              labelText: 'Avatar URL',
                              prefixIcon: Icon(Icons.person_outline),
                            ),
                          ),
                          const SizedBox(height: 12),
                          TextFormField(
                            controller: bannerCtrl,
                            decoration: const InputDecoration(
                              labelText: 'Banner URL',
                              prefixIcon: Icon(Icons.image_outlined),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    FilledButton.icon(
                      onPressed: () async {
                        final ok = formKey.currentState?.validate() ?? false;
                        if (!ok) return;

                        final verbosity = int.tryParse(verbosityCtrl.text.trim());
                        final interests = interestsCtrl.text
                            .split(',')
                            .map((e) => e.trim())
                            .where((e) => e.isNotEmpty)
                            .toList(growable: false);

                        await ref.read(authControllerProvider.notifier).updateProfile(
                              avatarUrl: avatarCtrl.text.trim().isEmpty ? null : avatarCtrl.text.trim(),
                              bannerUrl: bannerCtrl.text.trim().isEmpty ? null : bannerCtrl.text.trim(),
                              preferredName: preferredNameCtrl.text.trim().isEmpty ? null : preferredNameCtrl.text.trim(),
                              bio: bioCtrl.text.trim().isEmpty ? null : bioCtrl.text.trim(),
                              timezone: timezoneCtrl.text.trim().isEmpty ? null : timezoneCtrl.text.trim(),
                              uiTheme: uiTheme,
                              assistantTone: assistantTone,
                              assistantVerbosity: verbosity,
                              targetLanguage: targetLangCtrl.text.trim().isEmpty ? null : targetLangCtrl.text.trim(),
                              nativeLanguage: nativeLangCtrl.text.trim().isEmpty ? null : nativeLangCtrl.text.trim(),
                              interests: interests.isEmpty ? null : interests,
                            );

                        if (!sheetContext.mounted) return;
                        Navigator.of(sheetContext).pop(true);
                      },
                      icon: const Icon(Icons.save_outlined),
                      label: const Text('Save changes'),
                    ),
                    const SizedBox(height: 8),
                    OutlinedButton(
                      onPressed: () => Navigator.of(sheetContext).pop(false),
                      child: const Text('Cancel'),
                    ),
                  ],
                ),
              );
            },
          ),
        );
      },
    );

    if (saved == true && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Profile updated')));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authValue = ref.watch(authControllerProvider);
    final auth = authValue.valueOrNull;
    final user = auth?.user;

    if (authValue.isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (authValue.hasError) {
      return Scaffold(
        appBar: AppBar(title: const Text('Profile')),
        body: Center(child: Text(authValue.error.toString())),
      );
    }

    if (user == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Profile')),
        body: const Center(child: Text('No user data')),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        actions: [
          IconButton(
            onPressed: authValue.isLoading ? null : () => _showEditSheet(context, ref),
            icon: const Icon(Icons.edit_outlined),
            tooltip: 'Edit',
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
        children: [
          _ProfileHeader(
            username: user.username,
            email: user.email,
            preferredName: user.preferredName,
            bio: user.bio,
            avatarUrl: user.avatarUrl,
            bannerUrl: user.bannerUrl,
            xp: user.xp ?? 0,
            targetLanguage: user.targetLanguage,
            nativeLanguage: user.nativeLanguage,
            onChangeAvatar: () => _changeAvatar(context, ref),
            onChangeBanner: () => _changeBanner(context, ref),
          ),
          const SizedBox(height: 12),
          _SectionCard(
            title: 'My posts',
            child: Consumer(
              builder: (context, ref, _) {
                final postsValue = ref.watch(myPostsProvider);
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            'Recent',
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w700),
                          ),
                        ),
                        TextButton(
                          onPressed: () => context.push(Routes.myPosts),
                          child: const Text('View all'),
                        ),
                      ],
                    ),
                    postsValue.when(
                      loading: () => const Padding(
                        padding: EdgeInsets.symmetric(vertical: 8),
                        child: Center(child: CircularProgressIndicator()),
                      ),
                      error: (e, _) => Text(e.toString()),
                      data: (posts) {
                        if (posts.isEmpty) return const Text('No posts yet');

                        final preview = posts.take(3).toList(growable: false);
                        return Column(
                          children: [
                            for (final p in preview) ...[
                              ListTile(
                                contentPadding: EdgeInsets.zero,
                                title: Text(p.title.isEmpty ? 'Post' : p.title, maxLines: 1, overflow: TextOverflow.ellipsis),
                                subtitle: p.content.isEmpty
                                    ? null
                                    : Text(p.content, maxLines: 2, overflow: TextOverflow.ellipsis),
                                trailing: Text(p.isPublic ? 'PUBLIC' : 'PRIVATE'),
                              ),
                              if (p != preview.last) const Divider(height: 1),
                            ],
                          ],
                        );
                      },
                    ),
                  ],
                );
              },
            ),
          ),
          const SizedBox(height: 12),
          if ((user.interests ?? const <String>[]).isNotEmpty)
            _SectionCard(
              title: 'Interests',
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final it in (user.interests ?? const <String>[]))
                    Chip(
                      label: Text(it),
                      visualDensity: VisualDensity.compact,
                      backgroundColor: Theme.of(context).colorScheme.surfaceContainerHighest,
                    ),
                ],
              ),
            ),
          if ((user.interests ?? const <String>[]).isNotEmpty) const SizedBox(height: 12),
          _SectionCard(
            title: 'Preferences',
            child: Column(
              children: [
                _InfoRow(label: 'Timezone', value: user.timezone ?? 'UTC'),
                const SizedBox(height: 8),
                _InfoRow(label: 'UI theme', value: user.uiTheme ?? 'system'),
                const SizedBox(height: 8),
                _InfoRow(label: 'Selected theme', value: user.selectedThemeId ?? '—'),
                const SizedBox(height: 8),
                _InfoRow(label: 'Assistant tone', value: user.assistantTone ?? 'friendly'),
                const SizedBox(height: 8),
                _InfoRow(label: 'Verbosity', value: '${user.assistantVerbosity ?? 3}'),
              ],
            ),
          ),
          const SizedBox(height: 12),
          _SectionCard(
            title: 'Account',
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.edit_outlined),
                  title: const Text('Edit profile'),
                  subtitle: const Text('Name, languages, assistant settings'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => _showEditSheet(context, ref),
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.palette_outlined),
                  title: const Text('Themes'),
                  subtitle: const Text('Select UI theme palette'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push(Routes.themeSelect),
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.logout),
                  title: const Text('Logout'),
                  onTap: () => ref.read(authControllerProvider.notifier).logout(),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ProfileHeader extends StatelessWidget {
  const _ProfileHeader({
    required this.username,
    required this.email,
    required this.preferredName,
    required this.bio,
    required this.avatarUrl,
    required this.bannerUrl,
    required this.xp,
    required this.targetLanguage,
    required this.nativeLanguage,
    required this.onChangeAvatar,
    required this.onChangeBanner,
  });

  final String username;
  final String email;
  final String? preferredName;
  final String? bio;
  final String? avatarUrl;
  final String? bannerUrl;
  final int xp;
  final String? targetLanguage;
  final String? nativeLanguage;
  final VoidCallback onChangeAvatar;
  final VoidCallback onChangeBanner;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final bannerHeight = 140.0;

    return Card(
      child: ClipRRect(
        borderRadius: BorderRadius.circular(18),
        child: Column(
          children: [
            SizedBox(
              height: bannerHeight,
              width: double.infinity,
              child: Stack(
                fit: StackFit.expand,
                children: [
                  if ((bannerUrl ?? '').trim().isNotEmpty)
                    Image.network(
                      bannerUrl!.trim(),
                      fit: BoxFit.cover,
                      webHtmlElementStrategy: WebHtmlElementStrategy.prefer,
                      errorBuilder: (_, __, ___) => const SizedBox.shrink(),
                    ),
                  Positioned(
                    top: 10,
                    right: 10,
                    child: IconButton(
                      onPressed: onChangeBanner,
                      style: IconButton.styleFrom(
                        backgroundColor: Colors.black.withOpacity(0.35),
                        foregroundColor: Colors.white,
                      ),
                      icon: const Icon(Icons.photo_camera_outlined),
                      tooltip: 'Change banner',
                    ),
                  ),
                  DecoratedBox(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: [
                          scheme.primary.withOpacity(0.85),
                          scheme.secondary.withOpacity(0.55),
                        ],
                      ),
                    ),
                  ),
                  Align(
                    alignment: Alignment.bottomLeft,
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          _Avatar(avatarUrl: avatarUrl, fallback: username, onChange: onChangeAvatar),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  (preferredName ?? '').trim().isNotEmpty ? preferredName!.trim() : username,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                        fontWeight: FontWeight.w900,
                                        color: scheme.onPrimary,
                                      ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  email,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: scheme.onPrimary.withOpacity(0.9)),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if ((bio ?? '').trim().isNotEmpty)
                    Text(
                      bio!.trim(),
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  if ((bio ?? '').trim().isNotEmpty) const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: _MiniStat(
                          label: 'XP',
                          value: xp.toString(),
                          icon: Icons.bolt,
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: _MiniStat(
                          label: 'Target',
                          value: (targetLanguage ?? '—').trim().isEmpty ? '—' : (targetLanguage ?? '—'),
                          icon: Icons.flag_outlined,
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: _MiniStat(
                          label: 'Native',
                          value: (nativeLanguage ?? '—').trim().isEmpty ? '—' : (nativeLanguage ?? '—'),
                          icon: Icons.language_outlined,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Avatar extends StatelessWidget {
  const _Avatar({required this.avatarUrl, required this.fallback, required this.onChange});

  final String? avatarUrl;
  final String fallback;
  final VoidCallback onChange;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final url = (avatarUrl ?? '').trim();

    return Container(
      width: 56,
      height: 56,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: scheme.surface,
        border: Border.all(color: scheme.onPrimary.withOpacity(0.25), width: 1.2),
      ),
      child: Stack(
        children: [
          Positioned.fill(
            child: ClipOval(
              child: url.isEmpty
                  ? Center(
                      child: Text(
                        fallback.isEmpty ? '?' : fallback.characters.first.toUpperCase(),
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900),
                      ),
                    )
                  : Image.network(
                      url,
                      fit: BoxFit.cover,
                      webHtmlElementStrategy: WebHtmlElementStrategy.prefer,
                      errorBuilder: (_, __, ___) => Center(
                        child: Text(
                          fallback.isEmpty ? '?' : fallback.characters.first.toUpperCase(),
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900),
                        ),
                      ),
                    ),
            ),
          ),
          Positioned(
            right: -6,
            bottom: -6,
            child: IconButton(
              onPressed: onChange,
              style: IconButton.styleFrom(
                backgroundColor: Colors.black.withOpacity(0.35),
                foregroundColor: Colors.white,
              ),
              iconSize: 18,
              icon: const Icon(Icons.edit_outlined),
              tooltip: 'Change avatar',
            ),
          ),
        ],
      ),
    );
  }
}

class _MiniStat extends StatelessWidget {
  const _MiniStat({required this.label, required this.value, required this.icon});

  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Icon(icon, size: 18, color: scheme.onSurfaceVariant),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: Theme.of(context).textTheme.labelMedium?.copyWith(color: scheme.onSurfaceVariant)),
                const SizedBox(height: 2),
                Text(value, maxLines: 1, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  const _SectionCard({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
            const SizedBox(height: 10),
            child,
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Row(
      children: [
        Expanded(
          child: Text(
            label,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: scheme.onSurfaceVariant),
          ),
        ),
        const SizedBox(width: 12),
        Text(
          value,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w700),
        ),
      ],
    );
  }
}
