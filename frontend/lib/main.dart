import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'src/app/app.dart';
import 'src/core/di/locator.dart';
import 'src/core/env/env.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  const flavor = String.fromEnvironment('FLAVOR', defaultValue: 'dev');
  await dotenv.load(fileName: Env.fileForFlavor(flavor));

  setupLocator(Env.fromDotenv());

  runApp(const ProviderScope(child: App()));
}
