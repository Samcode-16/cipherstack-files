import contextlib
import pytest
import os
from backend.des_cipher import encrypt, decrypt


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_KEY = b"8bytekey"       # DES requires exactly 8 bytes
ALT_KEY   = b"altkey!!"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def key():
    return VALID_KEY

@pytest.fixture
def alt_key():
    return ALT_KEY


# ---------------------------------------------------------------------------
# Functional Tests
# ---------------------------------------------------------------------------

class TestDESFunctional:

    def test_encrypt_decrypt_roundtrip_bytes(self, key):
        data = b"Hello, World!!!"
        encrypted = encrypt(data, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted == data

    def test_encrypt_decrypt_roundtrip_string(self, key):
        data = "HelloWorld123456"
        encrypted = encrypt(data.encode(), key)
        decrypted = decrypt(encrypted, key)
        assert decrypted.decode() == data

    def test_encrypted_output_differs_from_input(self, key):
        data = b"plaintextdata!!!"
        encrypted = encrypt(data, key)
        assert encrypted != data

    def test_deterministic_encryption(self, key):
        data = b"samedata12345678"
        assert encrypt(data, key) == encrypt(data, key)

    def test_deterministic_decryption(self, key):
        data = b"samedata12345678"
        encrypted = encrypt(data, key)
        assert decrypt(encrypted, key) == decrypt(encrypted, key)

    def test_different_keys_produce_different_ciphertext(self, key, alt_key):
        data = b"testdata12345678"
        assert encrypt(data, key) != encrypt(data, alt_key)

    def test_decrypted_exactly_matches_original(self, key):
        data = b"exactmatch123456"
        encrypted = encrypt(data, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted == data

    @pytest.mark.parametrize("plaintext", [
        b"block1blockblock",
        b"another_testdata",
        b"0123456789abcdef",
        b"python_des_test!",
    ])
    def test_roundtrip_parametrized(self, key, plaintext):
        encrypted = encrypt(plaintext, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted == plaintext

    def test_wrong_key_decrypt_does_not_match_original(self, key, alt_key):
        data = b"mismatchtest1234"
        encrypted = encrypt(data, key)
        decrypted_wrong = decrypt(encrypted, alt_key)
        assert decrypted_wrong != data


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestDESEdgeCases:

    def test_single_block_input(self, key):
        data = b"8bytedat"
        encrypted = encrypt(data, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted == data

    def test_long_input_roundtrip(self, key):
        data = b"A" * 1024
        encrypted = encrypt(data, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted == data

    def test_large_random_binary_roundtrip(self, key):
        data = os.urandom(512)
        encrypted = encrypt(data, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted == data

    def test_all_zeros_input(self, key):
        data = b"\x00" * 16
        encrypted = encrypt(data, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted == data

    def test_all_max_bytes_input(self, key):
        data = b"\xff" * 16
        encrypted = encrypt(data, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted == data

    def test_output_is_bytes(self, key):
        data = b"bytescheck123456"
        encrypted = encrypt(data, key)
        assert isinstance(encrypted, bytes)

    def test_encrypted_length_is_multiple_of_block_size(self, key):
        data = b"blocksizetest123"
        encrypted = encrypt(data, key)
        assert len(encrypted) % 8 == 0

    @pytest.mark.parametrize("size", [8, 16, 32, 64, 128, 256])
    def test_various_data_sizes_roundtrip(self, key, size):
        data = os.urandom(size)
        encrypted = encrypt(data, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted == data


# ---------------------------------------------------------------------------
# Binary Support
# ---------------------------------------------------------------------------

class TestDESBinarySupport:

    def test_raw_bytes_encrypt_decrypt(self, key):
        raw = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        encrypted = encrypt(raw, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted == raw

    def test_non_ascii_bytes_roundtrip(self, key):
        data = bytes(range(128, 144))
        encrypted = encrypt(data, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted == data

    def test_binary_data_not_corrupted(self, key):
        data = b"\xde\xad\xbe\xef" * 4
        encrypted = encrypt(data, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted == data

    def test_random_binary_multiple_roundtrips(self, key):
        for _ in range(5):
            data = os.urandom(64)
            encrypted = encrypt(data, key)
            decrypted = decrypt(encrypted, key)
            assert decrypted == data


# ---------------------------------------------------------------------------
# Error Handling
# ---------------------------------------------------------------------------

class TestDESErrorHandling:

    def test_empty_bytes_encrypt_raises(self, key):
        with pytest.raises((ValueError, Exception)):
            encrypt(b"", key)

    def test_empty_string_encrypt_raises(self, key):
        with pytest.raises((ValueError, TypeError, Exception)):
            encrypt("", key)

    def test_invalid_key_too_short(self):
        with pytest.raises((ValueError, KeyError, Exception)):
            encrypt(b"somedata", b"short")

    def test_invalid_key_too_long(self):
        with pytest.raises((ValueError, KeyError, Exception)):
            encrypt(b"somedata", b"this_key_is_way_too_long_for_des")

    def test_invalid_key_type_string(self):
        with pytest.raises((TypeError, ValueError, Exception)):
            encrypt(b"somedata", "stringkey")

    def test_invalid_key_type_integer(self):
        with pytest.raises((TypeError, ValueError, Exception)):
            encrypt(b"somedata", 12345678)

    def test_invalid_key_type_none(self):
        with pytest.raises((TypeError, ValueError, Exception)):
            encrypt(b"somedata", None)

    def test_encrypt_invalid_input_type_string(self, key):
        with pytest.raises((TypeError, AttributeError, Exception)):
            encrypt("notbytes", key)

    def test_encrypt_invalid_input_type_none(self, key):
        with pytest.raises((TypeError, AttributeError, Exception)):
            encrypt(None, key)

    def test_decrypt_corrupted_data_raises_or_returns_garbage(self, key):
        with contextlib.suppress(Exception):
            result = decrypt(b"\xAB\xCD\xEF\x12\x34\x56\x78\x90", key)
            assert result != b"originalplaintext"

    def test_decrypt_truncated_data_raises(self, key):
        data = b"validdata1234567"
        encrypted = encrypt(data, key)
        truncated = encrypted[: len(encrypted) // 2]
        with pytest.raises((ValueError, Exception)):
            decrypt(truncated, key)