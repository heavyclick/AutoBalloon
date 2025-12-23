"""
Test script for FileService
"""
import sys
sys.path.insert(0, '/home/claude/autoballoon/backend')

from services.file_service import FileService, FileServiceError
from PIL import Image
import io

def test_file_service():
    service = FileService()
    
    # Test 1: Create a simple test image and process it
    print("Test 1: Processing PNG image...")
    test_image = Image.new('RGB', (800, 600), color='white')
    output = io.BytesIO()
    test_image.save(output, format='PNG')
    png_content = output.getvalue()
    
    try:
        result_bytes, format_type, width, height = service.process_file(png_content, "test.png")
        print(f"  ✓ Processed PNG: {width}x{height}, format: {format_type}")
        print(f"  ✓ Output size: {len(result_bytes)} bytes")
    except FileServiceError as e:
        print(f"  ✗ Error: {e.code} - {e.message}")
        return False
    
    # Test 2: Test base64 conversion
    print("\nTest 2: Base64 conversion...")
    b64_uri = service.to_base64(result_bytes)
    assert b64_uri.startswith("data:image/png;base64,")
    print(f"  ✓ Base64 URI created ({len(b64_uri)} chars)")
    
    # Test 3: Test thumbnail creation
    print("\nTest 3: Thumbnail creation...")
    thumbnail = service.create_thumbnail(result_bytes, max_width=100)
    assert thumbnail.startswith("data:image/jpeg;base64,")
    print(f"  ✓ Thumbnail created ({len(thumbnail)} chars)")
    
    # Test 4: Test file size validation
    print("\nTest 4: File size validation...")
    large_content = b"x" * (26 * 1024 * 1024)  # 26MB
    try:
        service.validate_file(large_content, "large.pdf")
        print("  ✗ Should have raised error for large file")
        return False
    except FileServiceError as e:
        assert e.code.value == "FILE_TOO_LARGE"
        print(f"  ✓ Correctly rejected large file: {e.message}")
    
    # Test 5: Test unsupported format
    print("\nTest 5: Unsupported format validation...")
    try:
        service.validate_file(b"test", "file.exe")
        print("  ✗ Should have raised error for unsupported format")
        return False
    except FileServiceError as e:
        assert e.code.value == "UNSUPPORTED_FORMAT"
        print(f"  ✓ Correctly rejected unsupported format: {e.message}")
    
    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    success = test_file_service()
    sys.exit(0 if success else 1)
