import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:focus_companion/utils/theme.dart';

class BrainInterfaceScreen extends StatefulWidget {
  const BrainInterfaceScreen({super.key});

  @override
  State<BrainInterfaceScreen> createState() => _BrainInterfaceScreenState();
}

class _BrainInterfaceScreenState extends State<BrainInterfaceScreen>
    with TickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _animation;
  
  final List<double> _focusData = [];
  final List<double> _stressData = [];
  final List<double> _timeData = [];
  
  Timer? _dataTimer;
  double _currentTime = 0;
  final Random _random = Random();

  @override
  void initState() {
    super.initState();
    
    // Initialize animation
    _animationController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );
    _animation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
    
    // Initialize data
    for (int i = 0; i < 50; i++) {
      _timeData.add(i.toDouble());
      _focusData.add(0.5 + 0.3 * sin(i * 0.2) + 0.1 * _random.nextDouble());
      _stressData.add(0.3 + 0.4 * sin(i * 0.15 + 1) + 0.1 * _random.nextDouble());
    }
    
    // Start real-time data collection
    _startDataCollection();
    _animationController.repeat();
  }

  void _startDataCollection() {
    _dataTimer = Timer.periodic(const Duration(milliseconds: 500), (timer) {
      if (mounted) {
        setState(() {
          _currentTime += 0.5;
          
          // Add new data points
          _timeData.add(_currentTime);
          _focusData.add(0.5 + 0.3 * sin(_currentTime * 0.2) + 0.1 * _random.nextDouble());
          _stressData.add(0.3 + 0.4 * sin(_currentTime * 0.15 + 1) + 0.1 * _random.nextDouble());
          
          // Remove old data points to keep the graph moving
          if (_timeData.length > 100) {
            _timeData.removeAt(0);
            _focusData.removeAt(0);
            _stressData.removeAt(0);
          }
        });
      }
    });
  }

  @override
  void dispose() {
    _animationController.dispose();
    _dataTimer?.cancel();
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
                // Header
                Row(
                  children: [
                    IconButton(
                      onPressed: () => Navigator.of(context).pop(),
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
                        color: AppTheme.primaryColor.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        '脑机接口',
                        style: AppTheme.bodyTextSecondary.copyWith(
                          color: AppTheme.primaryColor,
                        ),
                      ),
                    ),
                  ],
                ),
                
                const SizedBox(height: 32),
                
                // Title
                Text(
                  '实时脑电波监测',
                  style: AppTheme.heading2,
                  textAlign: TextAlign.center,
                ),
                
                const SizedBox(height: 8),
                
                Text(
                  '专注度与认知压力实时曲线',
                  style: AppTheme.bodyTextSecondary,
                  textAlign: TextAlign.center,
                ),
                
                const SizedBox(height: 32),
                
                // Focus Level Chart
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: AppTheme.cardDecoration,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            '专注度曲线',
                            style: AppTheme.bodyText.copyWith(
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 4,
                            ),
                            decoration: BoxDecoration(
                              color: AppTheme.accentColor.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              '${(_focusData.isNotEmpty ? _focusData.last * 100 : 0).round()}%',
                              style: AppTheme.bodyText.copyWith(
                                color: AppTheme.accentColor,
                                fontWeight: FontWeight.w600,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        height: 120,
                        child: CustomPaint(
                          size: const Size(double.infinity, 120),
                          painter: EEGPainter(
                            data: _focusData,
                            color: AppTheme.accentColor,
                            animation: _animation,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                
                const SizedBox(height: 24),
                
                // Cognitive Stress Chart
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: AppTheme.cardDecoration,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            '认知压力曲线',
                            style: AppTheme.bodyText.copyWith(
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 4,
                            ),
                            decoration: BoxDecoration(
                              color: AppTheme.errorColor.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              '${(_stressData.isNotEmpty ? _stressData.last * 100 : 0).round()}%',
                              style: AppTheme.bodyText.copyWith(
                                color: AppTheme.errorColor,
                                fontWeight: FontWeight.w600,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        height: 120,
                        child: CustomPaint(
                          size: const Size(double.infinity, 120),
                          painter: EEGPainter(
                            data: _stressData,
                            color: AppTheme.errorColor,
                            animation: _animation,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                
                const SizedBox(height: 32),
                
                // Status Indicators
                Row(
                  children: [
                    Expanded(
                      child: Container(
                        padding: const EdgeInsets.all(16),
                        decoration: AppTheme.cardDecoration,
                        child: Column(
                          children: [
                            Icon(
                              Icons.psychology,
                              color: AppTheme.accentColor,
                              size: 24,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              '脑电信号',
                              style: AppTheme.bodyTextSecondary.copyWith(
                                fontSize: 12,
                              ),
                            ),
                            Text(
                              '正常',
                              style: AppTheme.bodyText.copyWith(
                                color: AppTheme.accentColor,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Container(
                        padding: const EdgeInsets.all(16),
                        decoration: AppTheme.cardDecoration,
                        child: Column(
                          children: [
                            Icon(
                              Icons.sensors,
                              color: AppTheme.primaryColor,
                              size: 24,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              '采样频率',
                              style: AppTheme.bodyTextSecondary.copyWith(
                                fontSize: 12,
                              ),
                            ),
                            Text(
                              '256Hz',
                              style: AppTheme.bodyText.copyWith(
                                color: AppTheme.primaryColor,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
                
                const SizedBox(height: 40),
                
                // Back Button
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () => Navigator.of(context).pop(),
                    style: AppTheme.primaryButtonStyle.copyWith(
                      padding: WidgetStateProperty.all(
                        EdgeInsets.symmetric(vertical: 16),
                      ),
                    ),
                    child: Text(
                      '返回专注页面',
                      style: AppTheme.buttonText.copyWith(fontSize: 16),
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

class EEGPainter extends CustomPainter {
  final List<double> data;
  final Color color;
  final Animation<double> animation;

  EEGPainter({
    required this.data,
    required this.color,
    required this.animation,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty) return;

    final paint = Paint()
      ..color = color
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    final path = Path();
    final width = size.width;
    final height = size.height;
    final padding = 20.0;

    for (int i = 0; i < data.length; i++) {
      final x = (i / (data.length - 1)) * (width - 2 * padding) + padding;
      final y = height - padding - (data[i] * (height - 2 * padding));
      
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(EEGPainter oldDelegate) {
    return oldDelegate.data != data || oldDelegate.animation != animation;
  }
} 