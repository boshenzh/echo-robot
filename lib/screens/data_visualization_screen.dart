import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:focus_companion/providers/app_state.dart';
import 'package:focus_companion/utils/theme.dart';
import 'package:focus_companion/utils/formatters.dart';
import 'dart:math' as math;

class DataVisualizationScreen extends ConsumerStatefulWidget {
  const DataVisualizationScreen({super.key});

  @override
  ConsumerState<DataVisualizationScreen> createState() => _DataVisualizationScreenState();
}

class _DataVisualizationScreenState extends ConsumerState<DataVisualizationScreen>
    with TickerProviderStateMixin {
  late AnimationController _fadeController;
  late AnimationController _progressController;
  late AnimationController _cardController;
  late Animation<double> _fadeAnimation;
  late Animation<double> _progressAnimation;
  late Animation<double> _cardAnimation;
  
  int _currentMessageIndex = 0;

  // Mock data - in real app, this would come from database
  final int totalFocusMinutes = 1247;
  final int completedPromises = 23;
  final double trustScore = 0.78; // 0-1 scale
  final List<Map<String, dynamic>> weeklyData = [
    {'day': '周一', 'minutes': 45, 'promises': 2},
    {'day': '周二', 'minutes': 67, 'promises': 3},
    {'day': '周三', 'minutes': 38, 'promises': 1},
    {'day': '周四', 'minutes': 89, 'promises': 4},
    {'day': '周五', 'minutes': 56, 'promises': 2},
    {'day': '周六', 'minutes': 34, 'promises': 1},
    {'day': '周日', 'minutes': 72, 'promises': 3},
  ];

  @override
  void initState() {
    super.initState();
    
    _fadeController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    
    _progressController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );
    
    _cardController = AnimationController(
      duration: const Duration(milliseconds: 400),
      vsync: this,
    );
    
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeInOut,
    ));
    
    _progressAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _progressController,
      curve: Curves.easeOutCubic,
    ));
    
    _cardAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _cardController,
      curve: Curves.easeInOut,
    ));
    
    _fadeController.forward();
    _progressController.forward();
    _cardController.forward();
  }

  @override
  void dispose() {
    _fadeController.dispose();
    _progressController.dispose();
    _cardController.dispose();
    super.dispose();
  }
  
  void _nextMessage() {
    setState(() {
      _currentMessageIndex = (_currentMessageIndex + 1) % 4;
    });
    _cardController.reset();
    _cardController.forward();
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
                    Text(
                      '我的成长记录',
                      style: AppTheme.heading1.copyWith(
                        fontSize: 24,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const Spacer(),
                    const SizedBox(width: 48), // Balance the back button
                  ],
                ),
                
                const SizedBox(height: 32),
                
                // Main Stats Cards
                FadeTransition(
                  opacity: _fadeAnimation,
                  child: Column(
                    children: [
                      // Total Focus Time
                      _buildStatCard(
                        title: '总专注时长',
                        value: '${totalFocusMinutes}',
                        unit: '分钟',
                        icon: Icons.timer,
                        color: AppTheme.primaryColor,
                        subtitle: '约 ${(totalFocusMinutes / 60).round()} 小时',
                      ),
                      
                      const SizedBox(height: 16),
                      
                      // Completed Promises
                      _buildStatCard(
                        title: '完成承诺次数',
                        value: '$completedPromises',
                        unit: '次',
                        icon: Icons.check_circle,
                        color: AppTheme.accentColor,
                        subtitle: '对自己的承诺',
                      ),
                      
                      const SizedBox(height: 16),
                      
                      // Trust Score
                      _buildTrustScoreCard(),
                    ],
                  ),
                ),
                
                const SizedBox(height: 32),
                
                // Weekly Progress Chart
                FadeTransition(
                  opacity: _fadeAnimation,
                  child: _buildWeeklyChart(),
                ),
                
                const SizedBox(height: 32),
                
                // Motivational Message
                FadeTransition(
                  opacity: _fadeAnimation,
                  child: _buildMotivationalMessage(),
                ),
                
                const SizedBox(height: 40),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStatCard({
    required String title,
    required String value,
    required String unit,
    required IconData icon,
    required Color color,
    required String subtitle,
  }) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: AppTheme.cardDecoration.copyWith(
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Row(
        children: [
          Container(
            width: 60,
            height: 60,
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(30),
            ),
            child: Icon(
              icon,
              color: color,
              size: 28,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: AppTheme.bodyTextSecondary.copyWith(
                    fontSize: 14,
                  ),
                ),
                const SizedBox(height: 4),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      value,
                      style: AppTheme.heading2.copyWith(
                        color: color,
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(width: 4),
                    Text(
                      unit,
                      style: AppTheme.bodyText.copyWith(
                        color: color,
                        fontSize: 16,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: AppTheme.bodyTextSecondary.copyWith(
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTrustScoreCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: AppTheme.cardDecoration.copyWith(
        border: Border.all(color: AppTheme.accentColor.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  color: AppTheme.accentColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(25),
                ),
                child: const Icon(
                  Icons.psychology,
                  color: AppTheme.accentColor,
                  size: 24,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '安全感值',
                      style: AppTheme.bodyTextSecondary.copyWith(
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${(trustScore * 100).round()}%',
                      style: AppTheme.heading2.copyWith(
                        color: AppTheme.accentColor,
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      '对自己的信任感',
                      style: AppTheme.bodyTextSecondary.copyWith(
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          AnimatedBuilder(
            animation: _progressAnimation,
            builder: (context, child) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '信任度',
                        style: AppTheme.bodyText.copyWith(
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      Text(
                        '${(trustScore * 100).round()}%',
                        style: AppTheme.bodyText.copyWith(
                          fontSize: 12,
                          color: AppTheme.accentColor,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  LinearProgressIndicator(
                    value: trustScore * _progressAnimation.value,
                    backgroundColor: AppTheme.secondaryColor,
                    valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.accentColor),
                    minHeight: 8,
                  ),
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildWeeklyChart() {
    final maxMinutes = weeklyData.map((d) => d['minutes'] as int).reduce(math.max);
    
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: AppTheme.cardDecoration,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '本周专注趋势',
            style: AppTheme.bodyText.copyWith(
              fontWeight: FontWeight.w600,
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 20),
          SizedBox(
            height: 120,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: weeklyData.asMap().entries.map((entry) {
                final index = entry.key;
                final data = entry.value;
                final height = (data['minutes'] / maxMinutes) * 80;
                
                return AnimatedBuilder(
                  animation: _progressAnimation,
                  builder: (context, child) {
                    return Column(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Container(
                          width: 24,
                          height: height * _progressAnimation.value,
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.topCenter,
                              end: Alignment.bottomCenter,
                              colors: [
                                AppTheme.primaryColor,
                                AppTheme.primaryColor.withOpacity(0.6),
                              ],
                            ),
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          data['day'],
                          style: AppTheme.bodyTextSecondary.copyWith(
                            fontSize: 10,
                          ),
                        ),
                        Text(
                          '${data['minutes']}',
                          style: AppTheme.bodyTextSecondary.copyWith(
                            fontSize: 10,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    );
                  },
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMotivationalMessage() {
    final messages = [
      '每一次专注都是对自己的承诺',
      '你的坚持正在创造改变',
      '信任自己，你已经做得很好了',
      '好好休息，好好工作',
    ];
    
    final currentMessage = messages[_currentMessageIndex];
    
    return GestureDetector(
      onTap: _nextMessage,
      child: AnimatedBuilder(
        animation: _cardAnimation,
        builder: (context, child) {
          return Transform.scale(
            scale: 0.95 + (_cardAnimation.value * 0.05),
            child: Opacity(
              opacity: _cardAnimation.value,
              child: Container(
                padding: const EdgeInsets.all(20),
                decoration: AppTheme.cardDecoration.copyWith(
                  color: AppTheme.accentColor.withOpacity(0.08),
                  border: Border.all(color: AppTheme.accentColor.withOpacity(0.4)),
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.accentColor.withOpacity(0.2),
                      blurRadius: 12,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    Icon(
                      Icons.favorite,
                      color: AppTheme.accentColor.withOpacity(0.8),
                      size: 24,
                    ),
                    const SizedBox(height: 12),
                    Text(
                      currentMessage,
                      style: AppTheme.bodyText.copyWith(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.accentColor,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '点击切换',
                      style: AppTheme.bodyTextSecondary.copyWith(
                        fontSize: 12,
                        color: AppTheme.accentColor.withOpacity(0.6),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
} 