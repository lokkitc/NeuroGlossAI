class Routes {
  static const splash = '/';
  static const login = '/login';

  // Tabs
  static const home = '/home';
  static const chats = '/chats';
  static const characters = '/characters';
  static const memory = '/memory';
  static const profile = '/profile';

  // Chats
  static const chatSession = '/chats/:sessionId';

  // Characters
  static const characterCreate = '/characters/create';
  static const characterDetails = '/characters/:characterId';

  // Posts
  static const posts = '/home/posts';
  static const postCreate = '/home/posts/create';
  static const myPosts = '/home/posts/mine';

  // People
  static const publicUsers = '/home/users';

  // Themes
  static const themeSelect = '/profile/themes';

  // Public profiles
  static const publicUserProfile = '/u/:username';
}
