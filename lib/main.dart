import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:focus_companion/providers/app_state.dart';
import 'package:focus_companion/screens/home_screen.dart';
import 'package:focus_companion/screens/activation_screen.dart';
import 'package:focus_companion/screens/focus_setup_screen.dart';
import 'package:focus_companion/screens/focus_screen.dart';
import 'package:focus_companion/screens/break_screen.dart';
import 'package:focus_companion/utils/theme.dart';

void main() {
  runApp(const ProviderScope(child: FocusCompanionApp()));
}

class FocusCompanionApp extends ConsumerWidget {
  const FocusCompanionApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp(
      title: 'ECHOZON',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        fontFamily: 'Inter',
        primaryColor: AppTheme.primaryColor,
        scaffoldBackgroundColor: AppTheme.backgroundColor,
        colorScheme: ColorScheme.fromSeed(
          seedColor: AppTheme.primaryColor,
          background: AppTheme.backgroundColor,
          surface: AppTheme.surfaceColor,
        ),
        useMaterial3: true,
      ),
      home: const AppNavigator(),
    );
  }
}

class AppNavigator extends ConsumerWidget {
  const AppNavigator({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentScreen = ref.watch(appStateProvider);

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: AppTheme.backgroundGradient,
        ),
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 300),
          child: _buildScreen(currentScreen),
        ),
      ),
    );
  }

  Widget _buildScreen(AppScreen screen) {
    switch (screen) {
      case AppScreen.home:
        return const HomeScreen(key: ValueKey('home'));
      case AppScreen.activation:
        return const ActivationScreen(key: ValueKey('activation'));
      case AppScreen.focusSetup:
        return const FocusSetupScreen(key: ValueKey('focusSetup'));
      case AppScreen.focus:
        return const FocusScreen(key: ValueKey('focus'));
      case AppScreen.breakScreen:
        return const BreakScreen(key: ValueKey('break'));
    }
  }
}
