// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app_state.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$randomActivationTaskHash() =>
    r'c324f866552627d34b4aae7f7314fe57d8340b82';

/// See also [randomActivationTask].
@ProviderFor(randomActivationTask)
final randomActivationTaskProvider = AutoDisposeFutureProvider<Task>.internal(
  randomActivationTask,
  name: r'randomActivationTaskProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$randomActivationTaskHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef RandomActivationTaskRef = AutoDisposeFutureProviderRef<Task>;
String _$randomBreakTaskHash() => r'8bd1f84114b213ef990e5575ac1dc65331bde579';

/// See also [randomBreakTask].
@ProviderFor(randomBreakTask)
final randomBreakTaskProvider = AutoDisposeFutureProvider<Task>.internal(
  randomBreakTask,
  name: r'randomBreakTaskProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$randomBreakTaskHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef RandomBreakTaskRef = AutoDisposeFutureProviderRef<Task>;
String _$activationTasksHash() => r'0c825cf4ab431a8bdfa66de8b0551ca173ada022';

/// See also [activationTasks].
@ProviderFor(activationTasks)
final activationTasksProvider = AutoDisposeFutureProvider<List<Task>>.internal(
  activationTasks,
  name: r'activationTasksProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$activationTasksHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef ActivationTasksRef = AutoDisposeFutureProviderRef<List<Task>>;
String _$breakTasksHash() => r'235a295075940f9e561a762d7e355062a3f5520c';

/// See also [breakTasks].
@ProviderFor(breakTasks)
final breakTasksProvider = AutoDisposeFutureProvider<List<Task>>.internal(
  breakTasks,
  name: r'breakTasksProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$breakTasksHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef BreakTasksRef = AutoDisposeFutureProviderRef<List<Task>>;
String _$databaseServiceHash() => r'766f41a8fb8947216fae68bbc31fa62d037f6899';

/// See also [databaseService].
@ProviderFor(databaseService)
final databaseServiceProvider = AutoDisposeProvider<DatabaseService>.internal(
  databaseService,
  name: r'databaseServiceProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$databaseServiceHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef DatabaseServiceRef = AutoDisposeProviderRef<DatabaseService>;
String _$appStateHash() => r'61e8a857b0982103b63a9347caa010e7b5812884';

/// See also [AppState].
@ProviderFor(AppState)
final appStateProvider =
    AutoDisposeNotifierProvider<AppState, AppScreen>.internal(
      AppState.new,
      name: r'appStateProvider',
      debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
          ? null
          : _$appStateHash,
      dependencies: null,
      allTransitiveDependencies: null,
    );

typedef _$AppState = AutoDisposeNotifier<AppScreen>;
String _$focusTimerHash() => r'48c0f9789c79e9ce9071dd0006169e76a559aca2';

/// See also [FocusTimer].
@ProviderFor(FocusTimer)
final focusTimerProvider =
    AutoDisposeNotifierProvider<FocusTimer, Duration>.internal(
      FocusTimer.new,
      name: r'focusTimerProvider',
      debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
          ? null
          : _$focusTimerHash,
      dependencies: null,
      allTransitiveDependencies: null,
    );

typedef _$FocusTimer = AutoDisposeNotifier<Duration>;
String _$breakTimerHash() => r'0e507d13f5fa1c208401753e4243c0b5d88a5f6f';

/// See also [BreakTimer].
@ProviderFor(BreakTimer)
final breakTimerProvider =
    AutoDisposeNotifierProvider<BreakTimer, Duration>.internal(
      BreakTimer.new,
      name: r'breakTimerProvider',
      debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
          ? null
          : _$breakTimerHash,
      dependencies: null,
      allTransitiveDependencies: null,
    );

typedef _$BreakTimer = AutoDisposeNotifier<Duration>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
