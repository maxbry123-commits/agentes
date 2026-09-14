# Icons

`icon.png` is the source icon. The desktop project uses the same source image.
The platform icon bundle is generated with:

```sh
cd mobile && make ios-icons
```

That target runs `cargo tauri icon icons/icon.png --ios-color transparent`.
When the generated Xcode project exists, Tauri writes the iOS AppIcon PNGs into
`gen/apple/Assets.xcassets/AppIcon.appiconset/`. The generated desktop, Android,
and iOS icon outputs remain local build artifacts.
