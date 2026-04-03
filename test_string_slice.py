"""
Test Python string slicing for .encrypted removal
"""

# Test cases
test_filenames = [
    "temp_plaintext.encrypted",
    "test.encrypted",
    "file.encrypted",
    ".encrypted",
    "encrypted",
]

for filename in test_filenames:
    if filename.endswith('.encrypted'):
        result = filename[:-10]
        print(f"{filename:30} -> {result:20} (ends with .encrypted: True)")
    else:
        result = f"decrypted_{filename}"
        print(f"{filename:30} -> {result:20} (ends with .encrypted: False)")

# Manual count
test = "temp_plaintext.encrypted"
print(f"\nManual test: '{test}'")
print(f"Length: {len(test)}")
print(f"'.encrypted' length: {len('.encrypted')}")
print(f"test[:-10] = '{test[:-10]}'")
print(f"test[:-10] length: {len(test[:-10])}")
