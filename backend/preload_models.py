"""
Pre-download and cache all models used by DocIntel.

Run this once after installation to avoid re-downloading models:
    python preload_models.py

This will download:
1. Sentence transformer embedding model (~80MB)
2. Unstructured layout detection models (~160MB)
3. Table transformer model (~46MB)

Total: ~300MB

Models are cached in:
- Windows: C:\Users\<username>\.cache\huggingface\
- Linux/Mac: ~/.cache/huggingface/
"""

import os
import sys


def preload_embedding_model():
    """Pre-download sentence transformer model."""
    print("\n" + "="*60)
    print("1. Downloading Embedding Model")
    print("="*60)
    
    try:
        from sentence_transformers import SentenceTransformer
        from core.config import config
        
        print(f"Model: {config.EMBEDDING_MODEL_NAME}")
        print("Downloading... (this may take 1-2 minutes)")
        
        model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
        print(f"✅ Embedding model cached successfully")
        print(f"   Size: ~80MB")
        
        # Test it
        test_embedding = model.encode(["test sentence"])
        print(f"   Dimensions: {len(test_embedding[0])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to download embedding model: {e}")
        return False


def preload_unstructured_models():
    """Pre-download unstructured layout detection models."""
    print("\n" + "="*60)
    print("2. Downloading Unstructured Layout Models")
    print("="*60)
    
    try:
        from unstructured.partition.pdf import partition_pdf
        import tempfile
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        
        # Create a temporary test PDF
        print("Creating test PDF...")
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        
        c = canvas.Canvas(tmp_path, pagesize=letter)
        c.drawString(100, 750, "Test document for model download")
        c.save()
        
        print("Processing with hi-res strategy to trigger model download...")
        print("(This will download ~160MB of models)")
        
        # This will trigger the model downloads
        elements = partition_pdf(
            tmp_path,
            strategy="hi_res",
            extract_images_in_pdf=False,
            infer_table_structure=True,
        )
        
        # Cleanup
        os.unlink(tmp_path)
        
        print(f"✅ Layout detection models cached successfully")
        print(f"   Models: yolo_x_layout, resnet18, table-transformer")
        print(f"   Size: ~160MB")
        
        return True
        
    except ImportError as e:
        print(f"⚠️  Missing dependency: {e}")
        print(f"   Install with: pip install reportlab")
        return False
    except Exception as e:
        print(f"❌ Failed to download layout models: {e}")
        return False


def check_cache_location():
    """Show where models are cached."""
    print("\n" + "="*60)
    print("Cache Location")
    print("="*60)
    
    cache_dir = os.path.expanduser("~/.cache/huggingface")
    print(f"Models cached in: {cache_dir}")
    
    if os.path.exists(cache_dir):
        # Calculate total size
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(cache_dir):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                    file_count += 1
                except:
                    pass
        
        size_mb = total_size / (1024 * 1024)
        print(f"Total cache size: {size_mb:.1f} MB")
        print(f"Files: {file_count}")
    else:
        print("Cache directory doesn't exist yet")
    
    print("\nTo clear cache (if needed):")
    if os.name == 'nt':
        print(f'  Windows: rmdir /s /q "{cache_dir}"')
    else:
        print(f'  Linux/Mac: rm -rf "{cache_dir}"')


def main():
    """Pre-download all models."""
    print("\n" + "="*60)
    print("DocIntel Model Pre-loader")
    print("="*60)
    print("\nThis will download ~300MB of AI models.")
    print("Models are cached and only downloaded once.")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        return
    
    success_count = 0
    
    # 1. Embedding model
    if preload_embedding_model():
        success_count += 1
    
    # 2. Layout detection models
    if preload_unstructured_models():
        success_count += 1
    
    # 3. Show cache info
    check_cache_location()
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    if success_count == 2:
        print("✅ All models downloaded and cached successfully!")
        print("\nNext steps:")
        print("1. Start the backend: python main.py")
        print("2. Models will load instantly from cache")
        print("3. No more downloads during PDF processing")
    else:
        print(f"⚠️  {success_count}/2 model groups downloaded")
        print("\nSome models failed to download.")
        print("The system will try to download them when needed.")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
