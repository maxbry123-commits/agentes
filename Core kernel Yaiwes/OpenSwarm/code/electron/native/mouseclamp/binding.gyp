{
  "targets": [
    {
      "target_name": "mouseclamp",
      "sources": ["mouseclamp.mm"],
      "xcode_settings": {
        "CLANG_ENABLE_OBJC_ARC": "NO",
        "OTHER_CFLAGS": ["-fobjc-exceptions"]
      },
      "libraries": ["-framework Cocoa"],
      "conditions": [["OS!=\"mac\"", {"type": "none"}]]
    }
  ]
}
