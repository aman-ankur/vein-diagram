#!/usr/bin/env python3
"""
Dependency checker for PDF extraction test script.

This script verifies that all required dependencies are available
and provides setup instructions if anything is missing.
"""

import sys
import os
import subprocess
import importlib

def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    else:
        print(f"✅ Python {sys.version.split()[0]} is compatible")
        return True

def check_virtual_environment():
    """Check if virtual environment is active."""
    print("\n🔧 Checking virtual environment...")
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        print(f"✅ Virtual environment active: {venv_path}")
        return True
    else:
        print("⚠️  Virtual environment not detected")
        print("   Run: source vein-d/bin/activate")
        return False

def check_api_key():
    """Check if Anthropic API key is set."""
    print("\n🔑 Checking API key...")
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if api_key:
        print(f"✅ Anthropic API key is set ({api_key[:8]}...)")
        return True
    else:
        print("❌ ANTHROPIC_API_KEY environment variable not set")
        print("   Run: export ANTHROPIC_API_KEY='your_key_here'")
        return False

def check_package(package_name, import_name=None):
    """Check if a package is installed."""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name} - Run: pip install {package_name}")
        return False

def check_required_packages():
    """Check all required packages."""
    print("\n📦 Checking required packages...")
    
    packages = [
        ('PyPDF2', 'PyPDF2'),
        ('pdf2image', 'pdf2image'), 
        ('pytesseract', 'pytesseract'),
        ('pdfplumber', 'pdfplumber'),
        ('Pillow', 'PIL'),
        ('anthropic', 'anthropic'),
        ('sqlalchemy', 'sqlalchemy'),
        ('pandas', 'pandas'),
        ('dateutil', 'dateutil')
    ]
    
    all_good = True
    for package, import_name in packages:
        if not check_package(package, import_name):
            all_good = False
    
    return all_good

def check_tesseract():
    """Check if Tesseract OCR is available."""
    print("\n👁️  Checking Tesseract OCR...")
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ {version}")
            return True
        else:
            print("❌ Tesseract not working properly")
            return False
    except FileNotFoundError:
        print("❌ Tesseract not found")
        print("   Install: brew install tesseract (macOS) or apt-get install tesseract-ocr (Ubuntu)")
        return False

def check_backend_modules():
    """Check if backend modules are importable."""
    print("\n🏗️  Checking backend modules...")
    
    # Add backend to path
    backend_path = os.path.dirname(os.path.abspath(__file__))
    if backend_path not in sys.path:
        sys.path.append(backend_path)
    
    modules = [
        'app.services.pdf_service',
        'app.services.document_analyzer', 
        'app.services.utils.metrics',
        'app.services.utils.biomarker_cache',
        'app.core.config'
    ]
    
    all_good = True
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module} - {e}")
            all_good = False
    
    return all_good

def main():
    """Main dependency check function."""
    print("🔍 PDF Extraction Test - Dependency Check")
    print("=" * 50)
    
    checks = [
        check_python_version(),
        check_virtual_environment(), 
        check_api_key(),
        check_required_packages(),
        check_tesseract(),
        check_backend_modules()
    ]
    
    print("\n" + "=" * 50)
    
    if all(checks):
        print("🎉 All dependencies are ready!")
        print("\n✅ You can now run:")
        print("   python test_real_pdf_extraction.py your_file.pdf")
        return 0
    else:
        print("❌ Some dependencies are missing or misconfigured")
        print("\n📋 Setup checklist:")
        print("1. Activate virtual environment: source vein-d/bin/activate")
        print("2. Install missing packages: pip install -r requirements.txt")
        print("3. Set API key: export ANTHROPIC_API_KEY='your_key'")
        print("4. Install Tesseract OCR if needed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 