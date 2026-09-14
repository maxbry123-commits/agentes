// Trackpad haptic taps for dictation start/stop (and any future micro-feedback), the missing half
// of the WhisperFlow feel. NSHapticFeedbackManager only fires on Force Touch trackpads and only
// when macOS deems the app active; both are fine, this is garnish, never load-bearing.
//
// Fail-open everywhere: no trackpad, no permission, wrong thread, we return false and the app
// behaves exactly like today. macOS-only by binding.gyp condition.

#include <node_api.h>
#import <Cocoa/Cocoa.h>

static napi_value Perform(napi_env env, napi_callback_info info) {
  bool ok = false;
  @try {
    size_t argc = 1;
    napi_value argv[1];
    napi_get_cb_info(env, info, &argc, argv, NULL, NULL);
    int32_t pattern = 0;
    if (argc >= 1) napi_get_value_int32(env, argv[0], &pattern);
    NSHapticFeedbackPattern p = NSHapticFeedbackPatternGeneric;
    if (pattern == 1) p = NSHapticFeedbackPatternAlignment;
    else if (pattern == 2) p = NSHapticFeedbackPatternLevelChange;
    // Main-thread dispatch: AppKit feedback performers are main-thread creatures, and the IPC
    // handler that calls us already runs there in Electron's browser process; the async hop is
    // belt-and-suspenders for any future caller.
    dispatch_async(dispatch_get_main_queue(), ^{
      @try {
        [[NSHapticFeedbackManager defaultPerformer]
            performFeedbackPattern:p
                   performanceTime:NSHapticFeedbackPerformanceTimeNow];
      } @catch (NSException *e) { /* garnish only */ }
    });
    ok = true;
  } @catch (NSException *e) {
    ok = false;
  }
  napi_value result;
  napi_get_boolean(env, ok, &result);
  return result;
}

static napi_value Init(napi_env env, napi_value exports) {
  napi_value fn;
  napi_create_function(env, "perform", NAPI_AUTO_LENGTH, Perform, NULL, &fn);
  napi_set_named_property(env, exports, "perform", fn);
  return exports;
}

NAPI_MODULE(NODE_GYP_MODULE_NAME, Init)
