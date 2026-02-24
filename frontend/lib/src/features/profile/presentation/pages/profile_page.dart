import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../auth/presentation/controllers/auth_controller.dart';

class ProfilePage extends ConsumerWidget {
  const ProfilePage({super.key});

  Future<void> _showEditDialog(BuildContext context, WidgetRef ref) async {
    final auth = ref.read(authControllerProvider).valueOrNull;
    final user = auth?.user;
    if (user == null) return;

    final preferredNameCtrl = TextEditingController(text: user.preferredName ?? '');
    final avatarCtrl = TextEditingController(text: user.avatarUrl ?? '');
    final thumbnailCtrl = TextEditingController(text: user.thumbnailUrl ?? '');
    final bannerCtrl = TextEditingController(text: user.bannerUrl ?? '');
    final bioCtrl = TextEditingController(text: user.bio ?? '');
    final timezoneCtrl = TextEditingController(text: user.timezone ?? 'UTC');
    String uiTheme = user.uiTheme ?? 'system';
    String assistantTone = user.assistantTone ?? 'friendly';
    final verbosityCtrl = TextEditingController(text: (user.assistantVerbosity ?? 3).toString());

    final res = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('Edit profile'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: avatarCtrl,
                  decoration: const InputDecoration(labelText: 'Avatar URL'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: thumbnailCtrl,
                  decoration: const InputDecoration(labelText: 'Thumbnail URL'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: bannerCtrl,
                  decoration: const InputDecoration(labelText: 'Banner URL'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: preferredNameCtrl,
                  decoration: const InputDecoration(labelText: 'Preferred name'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: bioCtrl,
                  decoration: const InputDecoration(labelText: 'Bio'),
                  maxLines: 3,
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: timezoneCtrl,
                  decoration: const InputDecoration(labelText: 'Timezone'),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: uiTheme,
                  decoration: const InputDecoration(labelText: 'UI theme'),
                  items: const [
                    DropdownMenuItem(value: 'system', child: Text('System')),
                    DropdownMenuItem(value: 'light', child: Text('Light')),
                    DropdownMenuItem(value: 'dark', child: Text('Dark')),
                  ],
                  onChanged: (v) => uiTheme = v ?? 'system',
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: assistantTone,
                  decoration: const InputDecoration(labelText: 'Assistant tone'),
                  items: const [
                    DropdownMenuItem(value: 'friendly', child: Text('Friendly')),
                    DropdownMenuItem(value: 'neutral', child: Text('Neutral')),
                    DropdownMenuItem(value: 'strict', child: Text('Strict')),
                  ],
                  onChanged: (v) => assistantTone = v ?? 'friendly',
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: verbosityCtrl,
                  decoration: const InputDecoration(labelText: 'Assistant verbosity (1-10)'),
                  keyboardType: TextInputType.number,
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(false),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(dialogContext).pop(true),
              child: const Text('Save'),
            ),
          ],
        );
      },
    );

    if (res != true) return;

    final verbosity = int.tryParse(verbosityCtrl.text.trim());
    await ref.read(authControllerProvider.notifier).updateProfile(
          avatarUrl: avatarCtrl.text.trim().isEmpty ? null : avatarCtrl.text.trim(),
          thumbnailUrl: thumbnailCtrl.text.trim().isEmpty ? null : thumbnailCtrl.text.trim(),
          bannerUrl: bannerCtrl.text.trim().isEmpty ? null : bannerCtrl.text.trim(),
          preferredName: preferredNameCtrl.text.trim().isEmpty ? '' : preferredNameCtrl.text.trim(),
          bio: bioCtrl.text.trim(),
          timezone: timezoneCtrl.text.trim().isEmpty ? 'UTC' : timezoneCtrl.text.trim(),
          uiTheme: uiTheme,
          assistantTone: assistantTone,
          assistantVerbosity: verbosity,
        );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authValue = ref.watch(authControllerProvider);
    final auth = authValue.valueOrNull;
    final user = auth?.user;

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(user?.username ?? 'Unknown user', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          Text(user?.email ?? '', style: Theme.of(context).textTheme.bodyMedium),
          if ((user?.preferredName ?? '').isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(user!.preferredName!, style: Theme.of(context).textTheme.titleMedium),
          ],
          if ((user?.bio ?? '').isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(user!.bio!, style: Theme.of(context).textTheme.bodyMedium),
          ],
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: authValue.isLoading ? null : () => _showEditDialog(context, ref),
            icon: const Icon(Icons.edit),
            label: const Text('Edit profile'),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Preferences', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  Text('Timezone: ${user?.timezone ?? '-'}'),
                  Text('Theme: ${user?.uiTheme ?? '-'}'),
                  Text('Assistant tone: ${user?.assistantTone ?? '-'}'),
                  Text('Assistant verbosity: ${(user?.assistantVerbosity ?? 3)}'),
                  Text('Avatar URL: ${user?.avatarUrl ?? '-'}'),
                  Text('Thumbnail URL: ${user?.thumbnailUrl ?? '-'}'),
                  Text('Banner URL: ${user?.bannerUrl ?? '-'}'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: () => ref.read(authControllerProvider.notifier).logout(),
            icon: const Icon(Icons.logout),
            label: const Text('Logout'),
          ),
        ],
      ),
    );
  }
}
