---
name: flutter-app-evaluation
description: Use ALWAYS for Flutter projects — dispatches Flutter evaluator to test the running app on Android emulator and/or iOS simulator like a real user, checking UI, navigation, API integration, and persisted behavior via ADB/simctl.
---

# Flutter App Evaluation

Every Flutter feature with user-visible UI must be verified by a Flutter Evaluator that interacts with the running app on an emulator/simulator like a real user. Code review alone is insufficient — the app must be tapped, swiped, and tested on a device.

**Core principle:** If a user can't tap it and see it work on their phone, it's not done.

**This is non-negotiable for Flutter projects.**

## When This Applies

**Detection signals** (need at least 2, or 1 strong signal):
- Project has `pubspec.yaml` with `flutter` SDK dependency
- Files with `.dart` extension in `lib/` directory being modified
- User mentions "Flutter", "mobile app", "Android", "iOS", "widget"
- Project has `android/` and/or `ios/` directories

**Explicit exclusions (DO NOT trigger):**
- Dart CLI tools or server-side Dart (no Flutter SDK)
- Flutter packages/plugins with no runnable app
- Pure unit test changes with no UI impact
- `pubspec.yaml` dependency updates only

## Prerequisites

Before Flutter evaluation can run, the environment needs:

### Android
```bash
# Verify emulator is running
adb devices | grep -q "emulator"

# If not running, list and start one
emulator -list-avds
emulator -avd <avd_name> -no-window &

# Readiness probe: wait for boot
adb wait-for-device
adb shell getprop sys.boot_completed | grep -q "1"
```

### iOS (macOS only)
```bash
# Verify simulator is booted
xcrun simctl list devices booted | grep -q "Booted"

# If not booted, find and boot one
xcrun simctl list devices available | grep "iPhone"
xcrun simctl boot "iPhone 15 Pro"

# Readiness: simulator should be booted
xcrun simctl list devices booted
```

### Flutter App
```bash
# Build and run on target device
flutter run -d <device_id> &

# Readiness probe: wait for "Flutter run key commands" in output
# or check for app process
adb shell ps | grep -q "com.example.app"  # Android
xcrun simctl get_app_status booted com.example.app  # iOS
```

## The Evaluation Loop

```dot
digraph eval_loop {
    rankdir=TB;

    "Generator implements feature" [shape=box];
    "Code review passes (Codex CLI)" [shape=box];
    "Ensure emulator/simulator running" [shape=box];
    "Build and launch Flutter app" [shape=box];
    "Dispatch Flutter Evaluator" [shape=box style=filled fillcolor=lightyellow];
    "Evaluator tests app on device" [shape=box];
    "Verdict?" [shape=diamond];
    "Generator fixes issues" [shape=box];
    "Codex re-reviews fix code" [shape=box style=filled fillcolor=lightblue];
    "Feature complete" [shape=box style=filled fillcolor=lightgreen];

    "Generator implements feature" -> "Code review passes (Codex CLI)";
    "Code review passes (Codex CLI)" -> "Ensure emulator/simulator running";
    "Ensure emulator/simulator running" -> "Build and launch Flutter app";
    "Build and launch Flutter app" -> "Dispatch Flutter Evaluator";
    "Dispatch Flutter Evaluator" -> "Evaluator tests app on device";
    "Evaluator tests app on device" -> "Verdict?";
    "Verdict?" -> "Generator fixes issues" [label="FAIL or PASS_WITH_FIXES"];
    "Generator fixes issues" -> "Codex re-reviews fix code";
    "Codex re-reviews fix code" -> "Dispatch Flutter Evaluator" [label="re-evaluate"];
    "Verdict?" -> "Feature complete" [label="PASS"];
}
```

## How to Dispatch the Evaluator

### Step 1: Ensure device is running and app is built

```bash
# Android
adb devices | grep -q "emulator" || (emulator -avd <avd> -no-window & && adb wait-for-device)
flutter run -d emulator-5554 &
# Wait for app to launch
sleep 10 && adb shell ps | grep -q "com.example"

# iOS
xcrun simctl list devices booted | grep -q "Booted" || xcrun simctl boot "iPhone 15 Pro"
flutter run -d <simulator_id> &
sleep 10
```

### Step 2: Dispatch Flutter Evaluator

See `./flutter-evaluator-prompt.md` for the full dispatch template.

Key fields:
- **Target platform(s):** Android / iOS / Both
- **App package name:** e.g., `com.example.myapp`
- **What Was Built (CLAIM ONLY):** from implementer, labeled as unverified
- **Requirements (SOURCE OF TRUTH):** full task spec
- **Specific Test Scenarios:** concrete steps with expected outcomes

### Step 3: Act on the Verdict

| Verdict | Action |
|---------|--------|
| **PASS** | Feature complete. Proceed. |
| **PASS_WITH_FIXES** | Fix Important issues → Codex re-reviews → hot reload → re-evaluate |
| **FAIL** | Fix Critical issues → Codex re-reviews → hot restart → re-evaluate |

### Step 4: Re-evaluation with Hot Reload

Flutter's hot reload makes the fix-evaluate loop fast:

```bash
# After fix, if app is still running:
# Hot reload (preserves state)
adb shell input keyevent 82  # or send 'r' to flutter run process

# Hot restart (resets state)
# Send 'R' to flutter run process
```

**Terminal conditions (escalate to user when ANY is hit):**
- 3 consecutive FAIL verdicts on the same issues
- 3 consecutive PASS_WITH_FIXES where the same Important issue persists
- Total of 5 evaluation rounds on a single task
- The task may need to be re-scoped or the approach changed

## Integration with Subagent-Driven Development

```
Per Task (UI-visible):
1. Implementer builds feature (Claude)
2. Spec reviewer (Codex CLI) ✅
3. Code quality reviewer (Codex CLI) ✅
4. Start emulator/simulator + build app
5. Flutter Evaluator tests on device ✅
6. Mark task complete

Per Task (logic/data only — no UI):
1-3 same as above
4. Skip Flutter eval → mark complete
```

**Per-task Flutter evaluation:** Only when the task produces user-visible changes.
**Final full-app evaluation:** ALWAYS mandatory after all tasks — tests complete user journeys across both platforms.

## What the Evaluator Checks

### Functionality (FIRST PRIORITY)
- Every button/tap target works
- Forms validate and submit correctly
- Navigation: push, pop, tabs, drawers
- Loading states during async operations
- Error states display properly
- Pull-to-refresh, infinite scroll

### Platform-Specific
- **Android:** Back button behavior, material design conventions, status bar
- **iOS:** Swipe-to-go-back, cupertino widgets where expected, safe area
- **Both:** Platform-appropriate dialogs, date pickers, navigation patterns

### Robustness
- Rotation: portrait → landscape → portrait
- Background → foreground: state preserved?
- Dark mode: all text visible? Proper contrast?
- Empty states: what happens with no data?
- Keyboard: does it dismiss properly? Does it push content up?

### Technical Health
- Flutter errors in logs (RenderFlex overflow, setState after dispose)
- Jank/frame drops
- Memory warnings
- API failures
- Crash-free operation

### Visual Quality
- Consistent spacing, typography, colors
- Platform-appropriate design language
- No overflow, clipping, or misalignment
- Proper responsive behavior at different screen sizes

## Red Flags

**Never:**
- Skip Flutter evaluation for tasks with user-visible UI
- Trust the Generator's claim that "it works"
- Test on only one platform when both are available
- Give PASS with any Critical issues
- Give PASS with any Important issues
- Guess tap coordinates — always dump UI tree
- Ignore Flutter error logs
- Skip Codex re-review on fix code

**If app won't build/launch:**
- Check `flutter doctor` output
- Check build errors in logs
- Report as Critical blocker

## Why This Matters

Mobile apps have failure modes that code review cannot catch:
1. Touch targets too small or overlapping
2. Keyboard obscuring input fields
3. Rotation breaking layout
4. Platform-specific navigation expectations
5. Performance issues only visible on device
6. Dark mode making text invisible
7. The Generator is biased toward its own work
