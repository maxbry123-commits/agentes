# Windows Setup

## Configure OpenVINO
```bash
& 'C:\Program Files (x86)\Intel\openvino_2025.1.0\setupvars.ps1'
```

## CMake Compile
```bash
mkdir build
cd build
cmake ..
cmake --build . --config Release
.\Release\<binary_name>.exe <args...>
```