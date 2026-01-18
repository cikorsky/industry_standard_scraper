import PyInstaller.__main__
import os
import shutil
import sys
import dmgbuild

def build_app():
    print("🚀 Starting PyInstaller Build...")
    
    # 1. Clean previous builds
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')

    # 2. Define PyInstaller arguments
    args = [
        'gui_app.py',                       # Entry script
        '--name=IndustryScraper',           # App name
        '--windowed',                       # GUI mode (no console)
        '--noconfirm',                      # Overwrite output
        '--clean',                          # Clean cache
        
        # Data and Imports
        '--add-data=assets:assets',         # Include assets folder
        '--collect-all=ddddocr',            # Force collect ddddocr (if available)
        '--collect-all=playwright',         # Collect playwright package
        '--hidden-import=PIL',
        '--hidden-import=openpyxl',
        '--hidden-import=PySide6',          # Ensure PySide6 is found
    ]
    
    # Check for icon
    if os.path.exists('assets/icon.icns'):
        args.append('--icon=assets/icon.icns')
    
    # 3. Run PyInstaller
    PyInstaller.__main__.run(args)
    
    print("✅ Build finished! Checking output...")
    if not os.path.exists("dist/IndustryScraper.app"):
        print("❌ App bundle not found!")
        return

    # 4. Create DMG
    create_dmg()

def create_dmg():
    print("📦 Creating DMG...")
    app_path = os.path.abspath("dist/IndustryScraper.app")
    dmg_path = os.path.abspath("dist/IndustryScraper.dmg")
    vol_name = "Industry Scraper Installer"
    
    # Simple settings
    settings = {
        'files': [app_path],
        'symlinks': {'Applications': '/Applications'},
        'icon': 'assets/icon.icns' if os.path.exists('assets/icon.icns') else None
    }
    
    try:
        dmgbuild.build_dmg(dmg_path, vol_name, settings=settings)
        print(f"✅ DMG created successfully at: {dmg_path}")
    except Exception as e:
        print(f"❌ DMG creation failed: {e}")

if __name__ == "__main__":
    build_app()
