import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:focus_companion/providers/app_state.dart';
import 'package:focus_companion/utils/theme.dart';
import 'package:focus_companion/utils/formatters.dart';
import 'package:focus_companion/widgets/data_visualization_button.dart';
import 'dart:async'; // Added for Timer
import 'brain_interface_screen.dart';

class FocusScreen extends ConsumerStatefulWidget {
  const FocusScreen({super.key});

  @override
  ConsumerState<FocusScreen> createState() => _FocusScreenState();
}

class _FocusScreenState extends ConsumerState<FocusScreen>
    with TickerProviderStateMixin {
  late AnimationController _breathingController;
  late AnimationController _pulseController;
  late AnimationController _focusLevelController;
  late Animation<double> _breathingAnimation;
  late Animation<double> _pulseAnimation;
  late Animation<double> _focusLevelAnimation;

  // Simulated focus level for demo (in real app, this would come from BCI)
  double _focusLevel = 0.8;
  bool _isMonitoring = true;
  
  // Companion robot state
  bool _isEmojiAnimating = false;
  Timer? _emojiTimer;
  late AnimationController _bounceController;
  late Animation<double> _bounceAnimation;

  @override
  void initState() {
    super.initState();
    
    // Start the focus timer
    WidgetsBinding.instance.addPostFrameCallback((_) {
      // Get the duration from the app state (you might need to store this)
      ref.read(focusTimerProvider.notifier).start(20); // Default 20 minutes
    });

    // Breathing animation
    _breathingController = AnimationController(
      duration: const Duration(seconds: 4),
      vsync: this,
    );
    _breathingAnimation = Tween<double>(
      begin: 0.8,
      end: 1.2,
    ).animate(CurvedAnimation(
      parent: _breathingController,
      curve: Curves.easeInOut,
    ));

    // Pulse animation
    _pulseController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );
    _pulseAnimation = Tween<double>(
      begin: 1.0,
      end: 1.1,
    ).animate(CurvedAnimation(
      parent: _pulseController,
      curve: Curves.easeInOut,
    ));

    // Focus level animation
    _focusLevelController = AnimationController(
      duration: const Duration(seconds: 1),
      vsync: this,
    );
    _focusLevelAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _focusLevelController,
      curve: Curves.easeInOut,
    ));

    // Bounce animation for companion
    _bounceController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _bounceAnimation = Tween<double>(
      begin: 1.0,
      end: 1.2,
    ).animate(CurvedAnimation(
      parent: _bounceController,
      curve: Curves.elasticOut,
    ));

    // Start animations
    _breathingController.repeat(reverse: true);
    _pulseController.repeat(reverse: true);
    _focusLevelController.forward();

    // Simulate focus level changes (in real app, this would be BCI data)
    _startFocusMonitoring();
  }

  void _startFocusMonitoring() {
    Timer.periodic(const Duration(seconds: 3), (timer) {
      if (!_isMonitoring) {
        timer.cancel();
        return;
      }
      
      // Simulate focus level fluctuations
      setState(() {
        _focusLevel = 0.6 + (0.4 * (DateTime.now().millisecondsSinceEpoch % 100) / 100);
      });
      
      // If focus level drops too low, suggest a break
      if (_focusLevel < 0.3) {
        _suggestBreak();
      }
    });
  }

  void _suggestBreak() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('专注度提醒'),
        content: const Text('检测到专注度下降，建议现在休息一下。'),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
            },
            child: const Text('继续专注'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(context).pop();
              ref.read(focusTimerProvider.notifier).stop();
              ref.read(appStateProvider.notifier).completeFocusSession();
            },
            child: const Text('开始休息'),
          ),
        ],
      ),
    );
  }

  void _pokeCompanion() {
    if (_isEmojiAnimating) return;
    
    setState(() {
      _isEmojiAnimating = true;
    });
    
    // Trigger bounce animation
    _bounceController.forward().then((_) {
      _bounceController.reverse();
    });
    
    // Reset animation state after 3 seconds
    _emojiTimer?.cancel();
    _emojiTimer = Timer(const Duration(seconds: 3), () {
      if (mounted) {
        setState(() {
          _isEmojiAnimating = false;
        });
      }
    });
  }

  @override
  void dispose() {
    _breathingController.dispose();
    _pulseController.dispose();
    _focusLevelController.dispose();
    _bounceController.dispose();
    _emojiTimer?.cancel();
    _isMonitoring = false;
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final remainingTime = ref.watch(focusTimerProvider);

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
                // Header with progress indicator
                Row(
                  children: [
                    IconButton(
                      onPressed: () {
                        ref.read(focusTimerProvider.notifier).stop();
                        ref.read(appStateProvider.notifier).goHome();
                      },
                      icon: const Icon(
                        Icons.close,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    const Spacer(),
                    const DataVisualizationButton(),
                    const SizedBox(width: 8),
                    GestureDetector(
                      onTap: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (context) => const BrainInterfaceScreen(),
                          ),
                        );
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: AppTheme.surfaceColor,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: AppTheme.primaryColor.withOpacity(0.3),
                            width: 1,
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              width: 8,
                              height: 8,
                              decoration: BoxDecoration(
                                color: _focusLevel > 0.7 ? AppTheme.accentColor : AppTheme.errorColor,
                                borderRadius: BorderRadius.circular(4),
                              ),
                            ),
                            const SizedBox(width: 6),
                            Text(
                              '专注监测中',
                              style: AppTheme.bodyTextSecondary,
                            ),
                            const SizedBox(width: 4),
                            Icon(
                              Icons.arrow_forward_ios,
                              size: 12,
                              color: AppTheme.textSecondary,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
                
                const SizedBox(height: 32),
                
                // Timer Display
                AnimatedBuilder(
                  animation: _pulseAnimation,
                  builder: (context, child) {
                    return Transform.scale(
                      scale: _pulseAnimation.value,
                      child: Container(
                        padding: const EdgeInsets.all(40),
                        decoration: BoxDecoration(
                          color: AppTheme.surfaceColor,
                          borderRadius: BorderRadius.circular(40),
                          boxShadow: [
                            BoxShadow(
                              color: AppTheme.primaryColor.withOpacity(0.1),
                              blurRadius: 20,
                              offset: const Offset(0, 10),
                            ),
                          ],
                        ),
                        child: Column(
                          children: [
                            Text(
                              Formatters.formatDuration(remainingTime),
                              style: AppTheme.timerText,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              '剩余时间',
                              style: AppTheme.bodyTextSecondary,
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
                
                const SizedBox(height: 48),
                
                // Focus Level Indicator
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: AppTheme.cardDecoration,
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            '专注度',
                            style: AppTheme.bodyText.copyWith(
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          Text(
                            '${(_focusLevel * 100).round()}%',
                            style: AppTheme.bodyText.copyWith(
                              color: _focusLevel > 0.7 ? AppTheme.accentColor : AppTheme.errorColor,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      LinearProgressIndicator(
                        value: _focusLevel,
                        backgroundColor: AppTheme.secondaryColor,
                        valueColor: AlwaysStoppedAnimation<Color>(
                          _focusLevel > 0.7 ? AppTheme.accentColor : AppTheme.errorColor,
                        ),
                        minHeight: 8,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _focusLevel > 0.7 ? '专注状态良好' : '专注度偏低，建议调整',
                        style: AppTheme.bodyTextSecondary.copyWith(
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
                
                const SizedBox(height: 48),
                
                // Brain Interface Icon, Companion and Button (Same Level)
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    AnimatedBuilder(
                      animation: _breathingAnimation,
                      builder: (context, child) {
                        return Transform.scale(
                          scale: _breathingAnimation.value,
                          child: Container(
                            width: 60,
                            height: 60,
                            decoration: BoxDecoration(
                              color: AppTheme.accentColor.withOpacity(0.3),
                              borderRadius: BorderRadius.circular(30),
                            ),
                            child: Icon(
                              _focusLevel > 0.7 ? Icons.self_improvement : Icons.psychology,
                              size: 30,
                              color: AppTheme.accentColor,
                            ),
                          ),
                        );
                      },
                    ),
                    
                    Row(
                      children: [
                        AnimatedBuilder(
                          animation: _bounceAnimation,
                          builder: (context, child) {
                            return Transform.scale(
                              scale: _bounceAnimation.value,
                              child: Container(
                                width: 48,
                                height: 48,
                                decoration: BoxDecoration(
                                  borderRadius: BorderRadius.circular(24),
                                  color: AppTheme.surfaceColor,
                                  boxShadow: [
                                    BoxShadow(
                                      color: AppTheme.accentColor.withOpacity(0.2),
                                      blurRadius: 8,
                                      offset: const Offset(0, 2),
                                    ),
                                  ],
                                ),
                                child: ClipRRect(
                                  borderRadius: BorderRadius.circular(24),
                                  child: Image.asset(
                                    'assets/images/face.gif',
                                    width: 48,
                                    height: 48,
                                    fit: BoxFit.cover,
                                    repeat: ImageRepeat.noRepeat,
                                    gaplessPlayback: true,
                                    frameBuilder: (context, child, frame, wasSynchronouslyLoaded) {
                                      if (wasSynchronouslyLoaded) return child;
                                      return AnimatedOpacity(
                                        opacity: frame == null ? 0 : 1,
                                        duration: const Duration(milliseconds: 200),
                                        curve: Curves.easeInOut,
                                        child: child,
                                      );
                                    },
                                    errorBuilder: (context, error, stackTrace) {
                                      return Container(
                                        width: 48,
                                        height: 48,
                                        decoration: BoxDecoration(
                                          color: AppTheme.accentColor.withOpacity(0.2),
                                          borderRadius: BorderRadius.circular(24),
                                        ),
                                        child: const Icon(
                                          Icons.face,
                                          color: AppTheme.accentColor,
                                          size: 24,
                                        ),
                                      );
                                    },
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                        const SizedBox(width: 12),
                        ElevatedButton(
                          onPressed: _isEmojiAnimating ? null : _pokeCompanion,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.accentColor,
                            foregroundColor: AppTheme.surfaceColor,
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(20),
                            ),
                            elevation: 0,
                          ),
                          child: Text(
                            '戳戳小回',
                            style: AppTheme.bodyText.copyWith(
                              color: AppTheme.surfaceColor,
                              fontSize: 14,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
                
                const SizedBox(height: 16),
                
                Text(
                  _focusLevel > 0.7 ? '保持专注' : '深呼吸，重新集中',
                  style: AppTheme.bodyText.copyWith(
                    fontSize: 18,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                
                const SizedBox(height: 8),
                
                Text(
                  '脑机接口正在监测你的专注状态',
                  style: AppTheme.bodyTextSecondary,
                ),
                
                const Spacer(),
                
                // Control Buttons
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () {
                          ref.read(focusTimerProvider.notifier).stop();
                          ref.read(appStateProvider.notifier).completeFocusSession();
                        },
                        style: AppTheme.secondaryButtonStyle.copyWith(
                          padding: WidgetStateProperty.all(
                            EdgeInsets.symmetric(vertical: 16),
                          ),
                        ),
                        child: const Text(
                          '结束会话',
                          style: TextStyle(
                            color: AppTheme.textPrimary,
                            fontSize: 16,
                            fontWeight: FontWeight.w500,
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