import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../core/constants/routes.dart';

class AppShell extends StatelessWidget {
  const AppShell({super.key, required this.navigationShell});

  final StatefulNavigationShell navigationShell;

  int _indexForLocation(String location) {
    if (location.startsWith(Routes.chats)) return 1;
    if (location.startsWith(Routes.characters)) return 2;
    if (location.startsWith(Routes.memory)) return 3;
    if (location.startsWith(Routes.profile)) return 4;
    return 0;
  }

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    final currentIndex = _indexForLocation(location);

    return Scaffold(
      body: navigationShell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex,
        onDestinationSelected: (idx) {
          navigationShell.goBranch(idx, initialLocation: idx == navigationShell.currentIndex);
        },
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.chat_bubble_outline), selectedIcon: Icon(Icons.chat_bubble), label: 'Chats'),
          NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'Characters'),
          NavigationDestination(icon: Icon(Icons.memory_outlined), selectedIcon: Icon(Icons.memory), label: 'Memory'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: 'Profile'),
        ],
      ),
    );
  }
}
