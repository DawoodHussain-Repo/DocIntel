"""Quick test to check PDF extraction."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_pdf(pdf_path):
    print(f"\nTesting PDF: {pdf_path}")
    print("="*60)
    
    # Test 1: Check file exists
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    print(f"✅ File exists: {os.path.getsize(pdf_path)} bytes")
    
    # Test 2: Import unstructured
    try:
        from unstructured.partition.pdf import partition_pdf
        print("✅ Unstructured library imported")
    except ImportError as e:
        print(f"❌ Failed to import unstructured: {e}")
        return
    
    # Test 3: Try fast strategy
    print("\nTrying fast strategy...")
    try:
        elements = partition_pdf(
            pdf_path,
            strategy="fast",
            extract_images_in_pdf=False,
            infer_table_structure=False,
        )
        print(f"✅ Fast strategy returned {len(elements)} elements")
        
        valid = [e for e in elements if getattr(e, "text", "").strip()]
        print(f"   {len(valid)} elements have text")
        
        if valid:
            print(f"\n   First element text: {valid[0].text[:100]}...")
            print("\n✅ SUCCESS! PDF has extractable text with fast strategy")
            return True
        else:
            print("   ⚠️  No text found")
            
    except Exception as e:
        print(f"❌ Fast strategy error: {str(e)[:200]}")
    
    # Test 4: Try hi-res without OCR
    print("\nTrying hi-res (no OCR)...")
    try:
        elements = partition_pdf(
            pdf_path,
            strategy="hi_res",
            extract_images_in_pdf=False,
            infer_table_structure=True,
        )
        print(f"✅ Hi-res strategy returned {len(elements)} elements")
        
        valid = [e for e in elements if getattr(e, "text", "").strip()]
        print(f"   {len(valid)} elements have text")
        
        if valid:
            print(f"\n   First element text: {valid[0].text[:100]}...")
            print("\n✅ SUCCESS! PDF has extractable text with hi-res strategy")
            return True
        else:
            print("   ⚠️  No text found")
            
    except Exception as e:
        print(f"❌ Hi-res strategy error: {str(e)[:200]}")
    
    # Test 5: Check Tesseract
    print("\nChecking Tesseract...")
    import subprocess
    try:
        result = subprocess.run(
            ["tesseract", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ Tesseract found: {result.stdout.split()[1]}")
        else:
            print(f"⚠️  Tesseract issue: {result.stderr}")
    except Exception as e:
        print(f"❌ Tesseract not accessible: {e}")
    
    # Test 6: Try hi-res with OCR
    print("\nTrying hi-res with OCR...")
    try:
        # Set Tesseract path
        os.environ['TESSERACT_PATH'] = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        
        elements = partition_pdf(
            pdf_path,
            strategy="hi_res",
            extract_images_in_pdf=True,
            infer_table_structure=True,
        )
        print(f"✅ Hi-res with OCR returned {len(elements)} elements")
        
        valid = [e for e in elements if getattr(e, "text", "").strip()]
        print(f"   {len(valid)} elements have text")
        
        if valid:
            print(f"\n   First element text: {valid[0].text[:100]}...")
            print("\n✅ SUCCESS! PDF has extractable text with OCR")
            return True
        else:
            print("   ⚠️  No text found even with OCR")
            
    except Exception as e:
        print(f"❌ OCR strategy error: {str(e)[:300]}")
    
    print("\n" + "="*60)
    print("❌ All strategies failed")
    return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quick_test.py <path_to_pdf>")
        print("Example: python quick_test.py workspace/sample.pdf")
        sys.exit(1)
    
    test_pdf(sys.argv[1])
