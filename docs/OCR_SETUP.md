# OCR Setup for Scanned PDFs

DocIntel supports both text-based and scanned (image-based) PDFs. For scanned PDFs, OCR (Optical Character Recognition) is required.

---

## How It Works

DocIntel uses a smart fallback strategy:

1. **Fast Extraction (Default)**: Extracts embedded text from text-based PDFs
   - No OCR required
   - Fast processing
   - Works for most modern PDFs

2. **Hi-Res with OCR (Fallback)**: If no text is found, attempts OCR
   - Requires Tesseract OCR
   - Slower processing
   - Works for scanned documents

---

## Error Messages

### "The uploaded PDF does not contain extractable text"

**Cause**: The PDF is empty or corrupted.

**Solution**: Verify the PDF file is valid and contains content.

### "OCR is required but Tesseract is not installed"

**Cause**: The PDF is a scanned document (image-based) and Tesseract OCR is not installed.

**Solutions**:

#### Option 1: Install Tesseract (Recommended for Scanned PDFs)

**Windows:**
```powershell
# Using Chocolatey
choco install tesseract

# Or download installer from:
# https://github.com/UB-Mannheim/tesseract/wiki

# Add to PATH
$env:PATH += ";C:\Program Files\Tesseract-OCR"
```

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**Verify Installation:**
```bash
tesseract --version
```

#### Option 2: Convert PDF to Text-Based

Use a PDF editor to OCR the document before uploading:
- Adobe Acrobat Pro
- ABBYY FineReader
- Online OCR services

#### Option 3: Use Text-Based PDFs Only

Ensure all uploaded PDFs are text-based (not scanned images).

---

## Testing OCR

After installing Tesseract, restart the backend:

```bash
cd backend
python main.py
```

Upload a scanned PDF. You should see in the logs:

```json
{"event": "pdf_parsing_attempt", "strategy": "fast"}
{"event": "pdf_fast_extraction_empty"}
{"event": "pdf_parsing_attempt", "strategy": "hi_res"}
{"event": "pdf_parsing_success", "strategy": "hi_res"}
```

---

## Performance Considerations

| Strategy | Speed | Use Case |
|----------|-------|----------|
| Fast | ~1-2s | Text-based PDFs (90% of cases) |
| Hi-Res + OCR | ~10-30s | Scanned PDFs (10% of cases) |

**Recommendation**: For production with many scanned PDFs, consider:
1. Pre-processing PDFs with OCR before upload
2. Using a dedicated OCR service (AWS Textract, Google Vision)
3. Implementing async background processing for OCR

---

## Troubleshooting

### Tesseract Installed but Still Failing

**Check PATH:**
```bash
# Windows
echo $env:PATH

# macOS/Linux
echo $PATH
```

Tesseract must be in PATH for Python to find it.

**Restart Backend:**
After installing Tesseract, restart the backend server.

### OCR Quality Issues

**Install Language Data:**
```bash
# English (default)
# Already included with Tesseract

# Additional languages
# Windows: Download from Tesseract installer
# macOS: brew install tesseract-lang
# Linux: sudo apt-get install tesseract-ocr-[lang]
```

**Improve OCR Accuracy:**
- Use high-resolution scans (300 DPI minimum)
- Ensure good contrast and lighting
- Use clean, uncrumpled documents

### Memory Issues with Large PDFs

For PDFs > 50 pages with OCR:

1. **Increase Memory Limit:**
   ```bash
   # In .env
   MAX_FILE_SIZE_MB=50
   ```

2. **Use Chunked Processing:**
   Consider splitting large PDFs into smaller files.

---

## Alternative: Disable OCR Fallback

If you only want to support text-based PDFs:

Edit `backend/core/ingestion.py`:

```python
def process_pdf(file_path: str, filename: str, chroma_client: Any):
    # Remove the hi_res fallback logic
    elements = partition_pdf(
        file_path,
        strategy="fast",
        extract_images_in_pdf=False,
        infer_table_structure=False,
    )
    
    valid_elements = [e for e in elements if getattr(e, "text", "")]
    if not valid_elements:
        raise AppError(
            message="Only text-based PDFs are supported. Please OCR your document before uploading.",
            code="TEXT_BASED_ONLY",
            status_code=422,
        )
```

---

## Production Recommendations

### For Text-Based PDFs Only
- No Tesseract needed
- Fast processing
- Lower resource usage

### For Mixed PDFs (Text + Scanned)
- Install Tesseract
- Implement async processing
- Add progress indicators
- Consider caching OCR results

### For Heavy OCR Workloads
- Use dedicated OCR service (AWS Textract, Google Vision)
- Implement background job queue (Celery)
- Add retry logic for OCR failures
- Monitor OCR costs and usage

---

## API Error Codes

| Code | Status | Meaning |
|------|--------|---------|
| `EMPTY_DOCUMENT` | 422 | PDF has no extractable text |
| `OCR_NOT_AVAILABLE` | 422 | Scanned PDF but Tesseract not installed |
| `PDF_PARSE_FAILED` | 500 | PDF parsing failed for other reasons |

---

## Support

For issues with OCR setup:
1. Check Tesseract installation: `tesseract --version`
2. Check backend logs for detailed error messages
3. Verify PDF is not corrupted: Open in PDF reader
4. Try a different PDF to isolate the issue
