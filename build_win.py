import PyInstaller.__main__
import os
import shutil
import sys

def build_app():
    print("🚀 Starting PyInstaller Build for Windows...")
    
    # 1. Clean previous builds
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')

    # 2. Define PyInstaller arguments
    # Note: Windows uses ; for data separator
    args = [
        'gui_app.py',                       # Entry script
        '--name=IndustryScraper',           # App name
        '--windowed',                       # GUI mode (no console)
        '--noconfirm',                      # Overwrite output
        '--clean',                          # Clean cache
        
        # Data and Imports
        '--add-data=assets;assets',         # Include assets folder (Windows separator ;)
        '--collect-all=ddddocr',            # Force collect ddddocr
        '--collect-all=playwright',         # Collect playwright
        '--hidden-import=PIL',
        '--hidden-import=openpyxl',
        '--hidden-import=PySide6',
    ]
    
    # Check for icon (Windows uses .ico)
    if os.path.exists('assets/icon.ico'):
        args.append('--icon=assets/icon.ico')
    
    # 3. Run PyInstaller
    try:
        PyInstaller.__main__.run(args)
        print("✅ Build finished! You can find the executable in 'dist/IndustryScraper'")
        print("ℹ️  To create an MSI, use a tool like 'Advanced Installer' or 'WiX' on the 'dist' folder.")
    except Exception as e:
        print(f"❌ Build failed: {e}")

if __name__ == "__main__":
    if sys.platform != 'win32':
        print("⚠️  Warning: This script is intended for Windows. Paths/separators might be wrong on other OS.")
    build_app()
