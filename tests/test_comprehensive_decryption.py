#!/usr/bin/env python3
"""
Comprehensive encryption/decryption test with different input types.
Tests real-world scenarios including spaces, punctuation, case sensitivity, etc.
"""

import sys
from pathlib import Path
from backend import pipeline

def print_test_case(title, input_text, encrypted, decrypted, passed):
    """Print a formatted test case result."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"\n{status} | {title}")
    print(f"  Input:     '{input_text}'")
    print(f"  Decrypted: '{decrypted}'")
    if not passed:
        print(f"  ✗ Mismatch! Expected original text, got normalized/modified text")

def test_case_1():
    """Test: Simple text without special characters"""
    print("\n" + "="*80)
    print("TEST CASE 1: Simple text (no spaces, no punctuation)")
    print("="*80)
    
    input_text = "HELLO"
    encrypted = pipeline.encrypt_text(input_text)
    decrypted = pipeline.decrypt_text(encrypted)
    
    passed = decrypted == input_text
    print_test_case("Simple text", input_text, encrypted, decrypted, passed)
    return passed

def test_case_2():
    """Test: Text with spaces"""
    print("\n" + "="*80)
    print("TEST CASE 2: Text with spaces")
    print("="*80)
    
    input_text = "HELLO WORLD"
    encrypted = pipeline.encrypt_text(input_text)
    decrypted = pipeline.decrypt_text(encrypted)
    
    # Check if we get the original text back
    passed = decrypted == input_text
    
    print(f"Input length: {len(input_text)}")
    print(f"Decrypted length: {len(decrypted)}")
    print(f"Decrypted text: '{decrypted}'")
    print(f"Expected text: '{input_text}'")
    
    if not passed:
        # Check if spaces were removed
        normalized_input = input_text.replace(" ", "").upper()
        if decrypted == normalized_input:
            print(f"⚠ Spaces were removed during encryption (normalized to: '{normalized_input}')")
    
    print_test_case("Text with spaces", input_text, encrypted, decrypted, passed)
    return passed

def test_case_3():
    """Test: Lowercase text"""
    print("\n" + "="*80)
    print("TEST CASE 3: Lowercase text")
    print("="*80)
    
    input_text = "hello world"
    encrypted = pipeline.encrypt_text(input_text)
    decrypted = pipeline.decrypt_text(encrypted)
    
    # Check if we get the original text back
    passed = decrypted == input_text
    
    print(f"Input: '{input_text}' (lowercase)")
    print(f"Decrypted: '{decrypted}'")
    
    if not passed:
        # Check if case was changed
        uppercase_input = input_text.upper()
        if decrypted == uppercase_input:
            print(f"⚠ Text was converted to uppercase during encryption")
    
    print_test_case("Lowercase text", input_text, encrypted, decrypted, passed)
    return passed

def test_case_4():
    """Test: Text with punctuation"""
    print("\n" + "="*80)
    print("TEST CASE 4: Text with punctuation and numbers")
    print("="*80)
    
    input_text = "Hello, World! 123 & Test?"
    encrypted = pipeline.encrypt_text(input_text)
    decrypted = pipeline.decrypt_text(encrypted)
    
    passed = decrypted == input_text
    
    print(f"Input: '{input_text}'")
    print(f"Decrypted: '{decrypted}'")
    
    if not passed:
        # Check if only letters were kept
        import re
        letters_only = re.sub(r"[^A-Za-z]", "", input_text).upper()
        if decrypted == letters_only:
            print(f"⚠ Non-alphabetic characters were removed during encryption")
            print(f"   (Letters only: '{letters_only}')")
    
    print_test_case("Punctuation & numbers", input_text, encrypted, decrypted, passed)
    return passed

def test_case_5():
    """Test: Long text with spaces and mixed case"""
    print("\n" + "="*80)
    print("TEST CASE 5: Long text (mixed case, with spaces)")
    print("="*80)
    
    input_text = "The Quick Brown Fox Jumps Over The Lazy Dog"
    encrypted = pipeline.encrypt_text(input_text)
    decrypted = pipeline.decrypt_text(encrypted)
    
    passed = decrypted == input_text
    
    print(f"Input: '{input_text}'")
    print(f"Decrypted: '{decrypted}'")
    print(f"Input length: {len(input_text)}, Decrypted length: {len(decrypted)}")
    
    if not passed:
        import re
        normalized = re.sub(r"[^A-Za-z]", "", input_text).upper()
        if decrypted == normalized:
            print(f"⚠ Text was normalized (uppercase, no spaces): '{normalized}'")
    
    print_test_case("Long mixed text", input_text, encrypted, decrypted, passed)
    return passed

def test_case_6():
    """Test: Text with duplicate letters (triggers Playfair filler X)"""
    print("\n" + "="*80)
    print("TEST CASE 6: Text with duplicate letters (Playfair X filler test)")
    print("="*80)
    
    input_text = "HELLO"  # Contains LL
    encrypted = pipeline.encrypt_text(input_text)
    decrypted = pipeline.decrypt_text(encrypted)
    
    passed = decrypted == input_text
    
    print(f"Input: '{input_text}' (contains duplicate L's)")
    print(f"Decrypted: '{decrypted}'")
    
    if not passed:
        print(f"⚠ Issue with handling duplicate letters")
    
    print_test_case("Duplicate letters", input_text, encrypted, decrypted, passed)
    return passed

def test_case_7():
    """Test: File content encryption/decryption"""
    print("\n" + "="*80)
    print("TEST CASE 7: File content simulation")
    print("="*80)
    
    # Create a test file
    test_file = Path("test_input.txt")
    input_content = "This is a test message with spaces and lowercase letters."
    test_file.write_text(input_content, encoding='utf-8')
    
    # Read and encrypt
    file_content = test_file.read_text(encoding='utf-8')
    encrypted = pipeline.encrypt_text(file_content)
    decrypted = pipeline.decrypt_text(encrypted)
    
    passed = decrypted == file_content
    
    print(f"File content: '{file_content}'")
    print(f"Decrypted: '{decrypted}'")
    
    if not passed:
        import re
        normalized = re.sub(r"[^A-Za-z]", "", file_content).upper()
        if decrypted == normalized:
            print(f"⚠ File content was normalized (removed spaces, punctuation, changed case)")
    
    # Cleanup
    test_file.unlink()
    
    print_test_case("File content", input_content, encrypted, decrypted, passed)
    return passed

def main():
    print("\n" + "="*80)
    print("COMPREHENSIVE ENCRYPTION/DECRYPTION TEST SUITE")
    print("="*80)
    
    results = []
    results.append(("Simple text", test_case_1()))
    results.append(("Text with spaces", test_case_2()))
    results.append(("Lowercase text", test_case_3()))
    results.append(("Punctuation & numbers", test_case_4()))
    results.append(("Long mixed text", test_case_5()))
    results.append(("Duplicate letters", test_case_6()))
    results.append(("File content", test_case_7()))
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count < total_count:
        print("\n⚠ ISSUE IDENTIFIED:")
        print("The encryption/decryption pipeline normalizes input text:")
        print("  • Removes all non-alphabetic characters (spaces, punctuation, numbers)")
        print("  • Converts text to UPPERCASE")
        print("  • Returns normalized text on decryption")
        print("\nThis is by design - the Playfair cipher only works with letters.")
        print("To preserve original formatting, you need to:")
        print("  1. Store metadata about the original format")
        print("  2. Implement a wrapper that handles non-alphabetic characters")
        print("  3. Or document this as expected behavior")
        return 1
    else:
        print("\n✓ ALL TESTS PASSED")
        return 0

if __name__ == "__main__":
    sys.exit(main())
