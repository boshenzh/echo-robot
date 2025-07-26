import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:focus_companion/providers/app_state.dart';
import 'package:focus_companion/utils/theme.dart';
import 'package:focus_companion/widgets/data_visualization_button.dart';

class ActivationScreen extends ConsumerWidget {
  const ActivationScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final taskAsync = ref.watch(randomActivationTaskProvider);

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: AppTheme.backgroundGradient,
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              children: [
                // Header with Back Button and Data Button
                Row(
                  children: [
                    IconButton(
                      onPressed: () {
                        ref.read(appStateProvider.notifier).goHome();
                      },
                      icon: const Icon(
                        Icons.arrow_back_ios,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    const Spacer(),
                    const DataVisualizationButton(),
                  ],
                ),
                
                const Spacer(),
                
                // Task Card
                taskAsync.when(
                  data: (task) => Container(
                    padding: const EdgeInsets.all(32),
                    decoration: AppTheme.cardDecoration,
                    child: Column(
                      children: [
                        // Task Icon
                        Container(
                          width: 80,
                          height: 80,
                          decoration: BoxDecoration(
                            color: AppTheme.accentColor.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(40),
                          ),
                          child: const Icon(
                            Icons.touch_app,
                            size: 40,
                            color: AppTheme.accentColor,
                          ),
                        ),
                        
                        const SizedBox(height: 24),
                        
                        // Task Title
                        Text(
                          task.title,
                          style: AppTheme.heading2,
                          textAlign: TextAlign.center,
                        ),
                        
                        const SizedBox(height: 16),
                        
                        // Task Description
                        Text(
                          task.description,
                          style: AppTheme.bodyText.copyWith(
                            height: 1.5,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  ),
                  loading: () => Container(
                    padding: const EdgeInsets.all(32),
                    decoration: AppTheme.cardDecoration,
                    child: const Column(
                      children: [
                        CircularProgressIndicator(
                          color: AppTheme.primaryColor,
                        ),
                        SizedBox(height: 16),
                        Text(
                          '正在寻找你的任务...',
                          style: AppTheme.bodyText,
                        ),
                      ],
                    ),
                  ),
                  error: (error, stack) => Container(
                    padding: const EdgeInsets.all(32),
                    decoration: AppTheme.cardDecoration,
                    child: Column(
                      children: [
                        const Icon(
                          Icons.error_outline,
                          size: 48,
                          color: AppTheme.errorColor,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          '出现了一些问题',
                          style: AppTheme.bodyText,
                        ),
                      ],
                    ),
                  ),
                ),
                
                const SizedBox(height: 48),
                
                // Complete Button
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {
                      ref.read(appStateProvider.notifier).completeActivation();
                    },
                    style: AppTheme.primaryButtonStyle.copyWith(
                      padding: WidgetStateProperty.all(
                        EdgeInsets.symmetric(vertical: 20),
                      ),
                    ),
                                          child: Text(
                        '我已完成，简单～',
                        style: AppTheme.buttonText.copyWith(fontSize: 18),
                      ),
                  ),
                ),
                
                const SizedBox(height: 16),
                
                // Skip Button
                SizedBox(
                  width: double.infinity,
                  child: TextButton(
                    onPressed: () {
                      ref.read(appStateProvider.notifier).completeActivation();
                    },
                    child: Text(
                      '暂时跳过',
                      style: AppTheme.bodyTextSecondary.copyWith(
                        fontSize: 16,
                      ),
                    ),
                  ),
                ),
                
                const Spacer(),
              ],
            ),
          ),
        ),
      ),
    );
  }
} 