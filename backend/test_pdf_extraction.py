"""
Diagnostic script to test PDF extraction with different strategies.
Usage: python test_pdf_extraction.py <path_to_pdf>
"""
import sys
from pathlib import Path

def test_pdf_extraction(pdf_path: str):
    """Test PDF extraction with all strategies and show detailed results."""
    print(f"\n{'='*60}")
    print(f"Testing PDF: {pdf_path}")
    print(f"{'='*60}\n")
    
    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"❌ Error: File not found: {pdf_path}")
        return
    
    # Check file size
    file_size = Path(pdf_path).stat().st_size
    print(f"📄 File size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
    
    # Test imports
    print("\n1. Testing imports...")
    try:
        from unstructured.partition.pdf import partition_pdf
        print("   ✅ unstructured library imported successfully")
    except ImportError as e:
        print(f"   ❌ Failed to import unstructured: {e}")
        return
    
    # Test Tesseract
    print("\n2. Testing Tesseract...")
    import subprocess
    try:
        result = subprocess.run(
            ["tesseract", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"   ✅ Tesseract found: {version}")
        else:
            print(f"   ⚠️  Tesseract command failed: {result.stderr}")
    except FileNotFoundError:
        print("   ❌ Tesseract not found in PATH")
    except Exception as e:
        print(f"   ⚠️  Error checking Tesseract: {e}")
    
    # Strategy 1: Fast
    print("\n3. Testing Strategy 1: Fast (no OCR)...")
    try:
        elements = partition_pdf(
            pdf_path,
            strategy="fast",
            extract_images_in_pdf=False,
            infer_table_structure=False,
        )
        valid_elements = [e for e in elements if getattr(e, "text", "").strip()]
        print(f"   ✅ Fast strategy succeeded")
        print(f"   📊 Total elements: {len(elements)}")
        print(f"   📊 Valid elements (with text): {len(valid_elements)}")
        
        if valid_elements:
            print(f"\n   Sample text (first 200 chars):")
            sample_text = valid_elements[0].text[:200]
            print(f"   '{sample_text}...'")
            print(f"\n   ✅ SUCCESS: PDF has extractable text with fast strategy!")
            return
        else:
            print(f"   ⚠️  No text found with fast strategy")
            
    except Exception as e:
        print(f"   ❌ Fast strategy failed: {str(e)[:200]}")
    
    # Strategy 2: Hi-res without OCR
    print("\n4. Testing Strategy 2: Hi-Res (no OCR)...")
    try:
        elements = partition_pdf(
            pdf_path,
            strategy="hi_res",
            extract_images_in_pdf=False,
            infer_table_structure=True,
        )
        valid_elements = [e for e in elements if getattr(e, "text", "").strip()]
        print(f"   ✅ Hi-res (no OCR) strategy succeeded")
        print(f"   📊 Total elements: {len(elements)}")
        print(f"   📊 Valid elements (with text): {len(valid_elements)}")
        
        if valid_elements:
            print(f"\n   Sample text (first 200 chars):")
            sample_text = valid_elements[0].text[:200]
            print(f"   '{sample_text}...'")
            print(f"\n   ✅ SUCCESS: PDF has extractable text with hi-res strategy!")
            return
        else:
            print(f"   ⚠️  No text found with hi-res (no OCR) strategy")
            
    except Exception as e:
        print(f"   ❌ Hi-res (no OCR) strategy failed: {str(e)[:200]}")
    
    # Strategy 3: Hi-res with OCR
    print("\n5. Testing Strategy 3: Hi-Res with OCR...")
    try:
        elements = partition_pdf(
            pdf_path,
            strategy="hi_res",
            extract_images_in_pdf=True,
            infer_table_structure=True,
        )
        valid_elements = [e for e in elements if getattr(e, "text", "").strip()]
        print(f"   ✅ Hi-res with OCR strategy succeeded")
        print(f"   📊 Total elements: {len(elements)}")
        print(f"   📊 Valid elements (with text): {len(valid_elements)}")
        
        if valid_elements:
            print(f"\n   Sample text (first 200 chars):")
            sample_text = valid_elements[0].text[:200]
            print(f"   '{sample_text}...'")
            print(f"\n   ✅ SUCCESS: PDF has extractable text with OCR!")
            return
        else:
            print(f"   ⚠️  No text found even with OCR")
            
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ Hi-res with OCR strategy failed: {error_msg[:200]}")
        
        if "tesseract" in error_msg.lower():
            print(f"\n   💡 Tesseract issue detected!")
            print(f"   Please ensure:")
            print(f"   1. Tesseract is installed")
            print(f"   2. Tesseract is in your PATH")
            print(f"   3. Try: tesseract --version")
    
    print(f"\n{'='*60}")
    print(f"❌ FAILED: Could not extract text with any strategy")
    print(f"{'='*60}\n")
    print(f"Possible issues:")
    print(f"1. PDF is truly empty or corrupted")
    print(f"2. PDF uses unsupported encoding")
    print(f"3. PDF is encrypted or password-protected")
    print(f"4. Unstructured library version issue")
    print(f"\nTry:")
    print(f"- Open the PDF in a PDF reader to verify it has text")
    print(f"- Try a different PDF")
    print(f"- Check unstructured library version: pip show unstructured")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_pdf_extraction.py <path_to_pdf>")
        print("Example: python test_pdf_extraction.py sample_contract.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    test_pdf_extraction(pdf_path)
