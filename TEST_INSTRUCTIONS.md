# Testing PDF Extraction Issue

## Current Status

You have Tesseract installed at: `C:\Program Files\Tesseract-OCR`

The backend now auto-detects this path and should work with OCR.

## Steps to Test

### 1. Test with a Simple Text PDF

First, let's verify the system works with a known-good PDF:

```powershell
# In the backend directory with venv activated
cd backend
.\venv\Scripts\Activate.ps1

# Create a simple test PDF using Python
python -c "
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

c = canvas.Canvas('test_simple.pdf', pagesize=letter)
c.drawString(100, 750, 'This is a test contract.')
c.drawString(100, 730, 'Party A agrees to provide services.')
c.drawString(100, 710, 'Party B agrees to pay $1000.')
c.save()
print('Created test_simple.pdf')
"

# Test extraction
python quick_test.py test_simple.pdf
```

**Expected Result:** Should extract text with fast or hi-res strategy (no OCR needed)

### 2. Test Your Problematic PDF

```powershell
# Copy your PDF to the backend directory
Copy-Item "path\to\your\sample_contract_docintel.pdf" -Destination "."

# Test it
python quick_test.py sample_contract_docintel.pdf
```

**This will show:**
- Which strategy works (if any)
- Exact error messages
- Whether Tesseract is accessible

### 3. Check Backend Logs

When you upload through the UI, check the backend terminal for detailed logs:

```json
{"event": "pdf_parsing_attempt", "strategy": "fast"}
{"event": "pdf_fast_extraction_empty"}  // or "pdf_fast_strategy_failed"
{"event": "pdf_parsing_attempt", "strategy": "hi_res_no_ocr"}
{"event": "pdf_hi_res_no_ocr_empty"}  // or "pdf_hi_res_no_ocr_failed"
{"event": "pdf_attempting_ocr"}
{"event": "tesseract_path_set", "path": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"}
{"event": "pdf_parsing_attempt", "strategy": "hi_res_with_ocr"}
```

## Common Issues and Solutions

### Issue 1: "All strategies failed"

**Possible Causes:**
- PDF is encrypted or password-protected
- PDF uses unsupported encoding
- PDF is actually empty (no text layer)
- Unstructured library version issue

**Solutions:**
1. Open the PDF in Adobe Reader or browser - can you select/copy text?
2. Try a different PDF to verify the system works
3. Check unstructured version: `pip show unstructured`

### Issue 2: "Tesseract not found" (even though it's installed)

**Possible Causes:**
- PATH not updated in current session
- Python subprocess can't find tesseract.exe
- Permission issues

**Solutions:**
1. Restart PowerShell/terminal after installing Tesseract
2. Verify: `tesseract --version` works in PowerShell
3. Check the backend logs for "tesseract_path_set" message

### Issue 3: OCR takes too long (>30 seconds)

**This is normal for:**
- Large PDFs (>10 pages)
- High-resolution scanned images
- First OCR run (model loading)

**Solutions:**
- Be patient (OCR can take 1-2 minutes for large PDFs)
- Use smaller test PDFs first
- Consider pre-processing: reduce PDF size/resolution

## Debugging Your Specific PDF

To understand why `sample_contract_docintel.pdf` fails:

### Step 1: Verify it has text

```powershell
# Try to extract text with a simple tool
python -c "
import PyPDF2
with open('sample_contract_docintel.pdf', 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    print(f'Pages: {len(reader.pages)}')
    text = reader.pages[0].extract_text()
    print(f'First page text length: {len(text)}')
    print(f'Sample: {text[:200]}')
"
```

**If this shows text:** The PDF has a text layer, unstructured should work

**If this shows no text:** The PDF is image-based, needs OCR

### Step 2: Check PDF properties

```powershell
# Install pdfinfo (part of poppler-utils)
# Or use online tools like https://www.pdf-online.com/osa/validate.aspx

# Check:
# - Is it encrypted?
# - What's the PDF version?
# - Does it have fonts embedded?
```

### Step 3: Try with different unstructured version

```powershell
# Current version
pip show unstructured

# If issues, try updating
pip install --upgrade unstructured

# Or try specific version known to work
pip install unstructured==0.10.30
```

## Next Steps

1. **Run the quick_test.py on your PDF** and share the output
2. **Check if you can copy text** from the PDF in a PDF reader
3. **Try creating a simple test PDF** (using reportlab) and verify that works

Once we see the diagnostic output, we can identify the exact issue!

## Alternative: Use a Different PDF Library

If unstructured continues to fail, we can add a fallback using PyMuPDF:

```python
# Install
pip install pymupdf

# Test
python -c "
import fitz  # PyMuPDF
doc = fitz.open('sample_contract_docintel.pdf')
text = ''
for page in doc:
    text += page.get_text()
print(f'Extracted {len(text)} characters')
print(text[:500])
"
```

If this works, we can add it as a fallback strategy in the code.
