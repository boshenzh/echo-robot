import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:focus_companion/providers/app_state.dart';
import 'package:focus_companion/utils/theme.dart';
import 'package:focus_companion/widgets/data_visualization_button.dart';

class FocusSetupScreen extends ConsumerStatefulWidget {
  const FocusSetupScreen({super.key});

  @override
  ConsumerState<FocusSetupScreen> createState() => _FocusSetupScreenState();
}

class _FocusSetupScreenState extends ConsumerState<FocusSetupScreen> {
  RangeValues _timeRange = const RangeValues(15, 45);
  final TextEditingController _minController = TextEditingController();
  final TextEditingController _maxController = TextEditingController();

  final List<RangeValues> presetRanges = [
    const RangeValues(10, 30),
    const RangeValues(15, 45),
    const RangeValues(20, 60),
    const RangeValues(30, 90),
    const RangeValues(45, 120),
  ];

  @override
  void initState() {
    super.initState();
    _minController.text = _timeRange.start.round().toString();
    _maxController.text = _timeRange.end.round().toString();
  }

  @override
  void dispose() {
    _minController.dispose();
    _maxController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
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
                
                const SizedBox(height: 32),
                
                // Title
                Text(
                  '设置专注时间区间',
                  style: AppTheme.heading2,
                  textAlign: TextAlign.center,
                ),
                
                const SizedBox(height: 8),
                
                Text(
                  '系统会在最佳时机提醒你休息',
                  style: AppTheme.bodyTextSecondary,
                  textAlign: TextAlign.center,
                ),
                
                const SizedBox(height: 16),
                
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                  decoration: BoxDecoration(
                    color: AppTheme.accentColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: AppTheme.accentColor.withOpacity(0.3),
                      width: 1,
                    ),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.psychology,
                        color: AppTheme.accentColor,
                        size: 20,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          '小回会在此区间你专注度最低时提醒你休息，请放心去做',
                          style: AppTheme.bodyText.copyWith(
                            color: const Color(0xFF2E7D32), // 深绿色
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                
                const SizedBox(height: 48),
                
                // Time Range Display
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: AppTheme.cardDecoration,
                  child: Column(
                    children: [
                      Text(
                        '${_timeRange.start.round()} - ${_timeRange.end.round()} 分钟',
                        style: AppTheme.timerText.copyWith(
                          fontSize: 32,
                          color: AppTheme.primaryColor,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '专注时间区间',
                        style: AppTheme.bodyTextSecondary,
                      ),
                    ],
                  ),
                ),
                
                const SizedBox(height: 32),
                
                // Range Slider
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: AppTheme.cardDecoration,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '调整时间区间',
                        style: AppTheme.bodyText.copyWith(
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(height: 20),
                      RangeSlider(
                        values: _timeRange,
                        min: 5,
                        max: 180,
                        divisions: 35,
                        activeColor: AppTheme.primaryColor,
                        inactiveColor: AppTheme.secondaryColor,
                        labels: RangeLabels(
                          '${_timeRange.start.round()}分钟',
                          '${_timeRange.end.round()}分钟',
                        ),
                        onChanged: (RangeValues values) {
                          setState(() {
                            _timeRange = values;
                            _minController.text = values.start.round().toString();
                            _maxController.text = values.end.round().toString();
                          });
                        },
                      ),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _minController,
                              keyboardType: TextInputType.number,
                              decoration: AppTheme.inputDecoration.copyWith(
                                labelText: '最小时间',
                                suffixText: '分钟',
                              ),
                              onChanged: (value) {
                                final min = int.tryParse(value);
                                if (min != null && min >= 5 && min <= _timeRange.end) {
                                  setState(() {
                                    _timeRange = RangeValues(min.toDouble(), _timeRange.end);
                                  });
                                }
                              },
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: TextField(
                              controller: _maxController,
                              keyboardType: TextInputType.number,
                              decoration: AppTheme.inputDecoration.copyWith(
                                labelText: '最大时间',
                                suffixText: '分钟',
                              ),
                              onChanged: (value) {
                                final max = int.tryParse(value);
                                if (max != null && max >= _timeRange.start && max <= 180) {
                                  setState(() {
                                    _timeRange = RangeValues(_timeRange.start, max.toDouble());
                                  });
                                }
                              },
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                
                const SizedBox(height: 32),
                
                // Preset Ranges
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: AppTheme.cardDecoration,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '爱用设置',
                        style: AppTheme.bodyText.copyWith(
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Wrap(
                        spacing: 12,
                        runSpacing: 12,
                        children: presetRanges.map((range) {
                          final isSelected = _timeRange.start == range.start && 
                                           _timeRange.end == range.end;
                          return GestureDetector(
                            onTap: () {
                              setState(() {
                                _timeRange = range;
                                _minController.text = range.start.round().toString();
                                _maxController.text = range.end.round().toString();
                              });
                            },
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 16,
                                vertical: 12,
                              ),
                              decoration: BoxDecoration(
                                color: isSelected ? AppTheme.primaryColor : AppTheme.surfaceColor,
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(
                                  color: isSelected ? AppTheme.primaryColor : AppTheme.secondaryColor,
                                  width: 1,
                                ),
                              ),
                              child: Text(
                                '${range.start.round()}-${range.end.round()}',
                                style: AppTheme.bodyText.copyWith(
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
                
                const SizedBox(height: 40),
                
                // Start Focus Session Button
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {
                      // For now, we'll use the average of the range
                      final averageDuration = ((_timeRange.start + _timeRange.end) / 2).round();
                      ref.read(appStateProvider.notifier).startFocusSession(averageDuration);
                    },
                    style: AppTheme.primaryButtonStyle.copyWith(
                      padding: WidgetStateProperty.all(
                        EdgeInsets.symmetric(vertical: 20),
                      ),
                    ),
                    child: Text(
                      '开始专注区间 ${_timeRange.start.round()}-${_timeRange.end.round()} 分钟',
                      style: AppTheme.buttonText.copyWith(fontSize: 18),
                    ),
                  ),
                ),
                
                const SizedBox(height: 16),
                
                // Back Button
                SizedBox(
                  width: double.infinity,
                  child: TextButton(
                    onPressed: () {
                      ref.read(appStateProvider.notifier).navigateTo(AppScreen.activation);
                    },
                    child: Text(
                      '返回激活任务',
                      style: AppTheme.bodyTextSecondary.copyWith(
                        fontSize: 16,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
} 