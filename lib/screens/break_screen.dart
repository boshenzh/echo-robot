import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:focus_companion/providers/app_state.dart';
import 'package:focus_companion/utils/theme.dart';
import 'package:focus_companion/widgets/data_visualization_button.dart';
import 'package:focus_companion/utils/formatters.dart';

class BreakScreen extends ConsumerStatefulWidget {
  const BreakScreen({super.key});

  @override
  ConsumerState<BreakScreen> createState() => _BreakScreenState();
}

class _BreakScreenState extends ConsumerState<BreakScreen> {
  int _breakDuration = 3; // Default 3 minutes
  final TextEditingController _durationController = TextEditingController();
  
  final List<int> presetDurations = [1, 2, 3, 5, 8, 10, 15];

  @override
  void initState() {
    super.initState();
    _durationController.text = _breakDuration.toString();
    
    // Start the break timer when the screen loads
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(breakTimerProvider.notifier).start(_breakDuration);
    });
  }

  @override
  void dispose() {
    _durationController.dispose();
    super.dispose();
  }

  void _updateBreakDuration(int duration) {
    setState(() {
      _breakDuration = duration;
      _durationController.text = duration.toString();
    });
    
    // Restart timer with new duration
    ref.read(breakTimerProvider.notifier).stop();
    ref.read(breakTimerProvider.notifier).start(duration);
  }

  @override
  Widget build(BuildContext context) {
    final taskAsync = ref.watch(randomBreakTaskProvider);
    final remainingTime = ref.watch(breakTimerProvider);

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: AppTheme.backgroundGradient,
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
                                  child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          // Header with Back Button, Data Button and Break Time Label
                          Row(
                            children: [
                              IconButton(
                                onPressed: () {
                                  ref.read(breakTimerProvider.notifier).stop();
                                  ref.read(appStateProvider.notifier).goHome();
                                },
                                icon: const Icon(
                                  Icons.arrow_back_ios,
                                  color: AppTheme.textPrimary,
                                ),
                              ),
                              const Spacer(),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                  vertical: 6,
                                ),
                                decoration: BoxDecoration(
                                  color: AppTheme.accentColor.withOpacity(0.2),
                                  borderRadius: BorderRadius.circular(20),
                                ),
                                child: Text(
                                  '休息时间',
                                  style: AppTheme.bodyTextSecondary.copyWith(
                                    color: AppTheme.accentColor,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 12),
                              const DataVisualizationButton(),
                            ],
                          ),
                
                const SizedBox(height: 32),
                
                // Break Task Card
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
                            Icons.coffee,
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
                          'Finding your break activity...',
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
                
                const SizedBox(height: 32),
                
                // Break Duration Settings
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: AppTheme.cardDecoration,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '休息时长设置',
                        style: AppTheme.bodyText.copyWith(
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(height: 16),
                      
                      // Custom Duration Input
                      TextField(
                        controller: _durationController,
                        keyboardType: TextInputType.number,
                        decoration: AppTheme.inputDecoration.copyWith(
                          labelText: '自定义休息时长',
                          suffixText: '分钟',
                          hintText: '输入分钟数',
                        ),
                        onChanged: (value) {
                          final duration = int.tryParse(value);
                          if (duration != null && duration > 0 && duration <= 60) {
                            _updateBreakDuration(duration);
                          }
                        },
                      ),
                      
                      const SizedBox(height: 16),
                      
                      // Preset Durations
                      Text(
                        '快速选择',
                        style: AppTheme.bodyTextSecondary.copyWith(
                          fontSize: 14,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: presetDurations.map((duration) {
                          final isSelected = _breakDuration == duration;
                          return GestureDetector(
                            onTap: () => _updateBreakDuration(duration),
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 8,
                              ),
                              decoration: BoxDecoration(
                                color: isSelected ? AppTheme.accentColor : AppTheme.surfaceColor,
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(
                                  color: isSelected ? AppTheme.accentColor : AppTheme.secondaryColor,
                                  width: 1,
                                ),
                              ),
                              child: Text(
                                '${duration}分钟',
                                style: AppTheme.bodyText.copyWith(
                                  fontSize: 12,
                                  color: isSelected ? AppTheme.surfaceColor : AppTheme.textPrimary,
                                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                                ),
                              ),
                            ),
                          );
                        }).toList(),
                      ),
                    ],
                  ),
                ),
                
                const SizedBox(height: 32),
                
                // Break Timer
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: AppTheme.accentColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Column(
                    children: [
                      Text(
                        Formatters.formatDuration(remainingTime),
                        style: AppTheme.timerText.copyWith(
                          fontSize: 36,
                          color: AppTheme.accentColor,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '休息时间剩余',
                        style: AppTheme.bodyTextSecondary.copyWith(
                          color: AppTheme.accentColor,
                        ),
                      ),
                    ],
                  ),
                ),
                
                const SizedBox(height: 40),
                
                // Action Buttons
                Column(
                  children: [
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: () {
                          ref.read(breakTimerProvider.notifier).stop();
                          ref.read(appStateProvider.notifier).completeBreak();
                        },
                        style: AppTheme.primaryButtonStyle.copyWith(
                          padding: WidgetStateProperty.all(
                            EdgeInsets.symmetric(vertical: 16),
                          ),
                        ),
                        child: Text(
                          '开始另一个会话',
                          style: AppTheme.buttonText.copyWith(fontSize: 16),
                        ),
                      ),
                    ),
                    
                    const SizedBox(height: 12),
                    
                    SizedBox(
                      width: double.infinity,
                      child: TextButton(
                        onPressed: () {
                          ref.read(breakTimerProvider.notifier).stop();
                          ref.read(appStateProvider.notifier).goHome();
                        },
                        child: Text(
                          '我完成了',
                          style: AppTheme.bodyTextSecondary.copyWith(
                            fontSize: 16,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
} 