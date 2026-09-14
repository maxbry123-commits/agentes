#!/usr/bin/env python3
"""
Test script to verify ISEK installation and setup process.
This script can be run to test the complete installation flow.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description, check=True):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return result.stdout
        else:
            print(f"❌ {description} failed")
            print(f"Error: {result.stderr}")
            if check:
                sys.exit(1)
            return None
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        if check:
            sys.exit(1)
        return None


def test_installation():
    """Test the complete installation process"""
    print("🚀 Testing ISEK installation process...")
    print("=" * 50)

    # Test 1: Check Python version
    python_version = run_command("python --version", "Checking Python version")
    if python_version and (
        "3.10" not in python_version
        and "3.11" not in python_version
        and "3.12" not in python_version
    ):
        print("⚠️  Warning: Python 3.10+ is recommended")

    # Test 2: Check if ISEK is installed
    try:
        import isek

        print("✅ ISEK package is installed")
    except ImportError:
        print("❌ ISEK package is not installed")
        print("Run: pip install isek")
        sys.exit(1)

    # Test 3: Check CLI availability
    cli_output = run_command("isek --help", "Testing CLI availability")
    if cli_output and "ISEK Distributed Multi-Agent Framework CLI" not in cli_output:
        print("❌ CLI not working correctly")
        sys.exit(1)

    # Test 4: Test setup command
    print("🔧 Testing setup command...")
    try:
        # Run setup in a subprocess to avoid affecting current environment
        result = subprocess.run(
            [sys.executable, "-m", "isek.cli", "setup"],
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
        )
        if result.returncode == 0:
            print("✅ Setup command completed successfully")
        else:
            print(f"⚠️  Setup command had issues: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("⚠️  Setup command timed out (this might be normal)")
    except Exception as e:
        print(f"⚠️  Setup command failed: {e}")

    # Test 5: Check for P2P files
    isek_path = Path(isek.__file__).parent
    p2p_path = isek_path / "protocol" / "p2p"

    if p2p_path.exists():
        print("✅ P2P directory found")

        # Check for package.json
        if (p2p_path / "package.json").exists():
            print("✅ package.json found")
        else:
            print("❌ package.json not found")

        # Check for JavaScript files
        js_files = list(p2p_path.glob("*.js"))
        if js_files:
            print(f"✅ Found {len(js_files)} JavaScript files")
        else:
            print("❌ No JavaScript files found")
    else:
        print("❌ P2P directory not found")

    # Test 6: Test example listing
    example_output = run_command("isek example list", "Testing example listing")
    if example_output and "Available examples:" in example_output:
        print("✅ Example listing works")
    else:
        print("❌ Example listing failed")

    print("\n" + "=" * 50)
    print("🎉 Installation test completed!")
    print("\nNext steps:")
    print("1. Set up your .env file with API keys")
    print("2. Run 'isek example run lv1_single_agent' to test")
    print("3. Check out the documentation for more examples")


if __name__ == "__main__":
    test_installation()
