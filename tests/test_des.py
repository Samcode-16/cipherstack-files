"""Unit tests for backend/des_cipher.py"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.des_cipher import (
    encrypt, decrypt, get_key_info,
    _validate_des_key, _pad_plaintext_des, _unpad_plaintext_des
)


class TestValidateDESKey:
    def test_valid_key_returns_bytes(self):
        key = _validate_des_key("0123456789abcdef")
        assert isinstance(key, bytes)
        assert len(key) == 8

    def test_wrong_length_raises(self):
        with pytest.raises(ValueError):
            _validate_des_key("0123456789ab")  # 12 chars, not 16

    def test_non_hex_raises(self):
        with pytest.raises(ValueError):
            _validate_des_key("0123456789abcxyz")

    def test_non_string_raises(self):
        with pytest.raises(ValueError):
            _validate_des_key(12345678)

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            _validate_des_key("")

    def test_uppercase_hex_accepted(self):
        key = _validate_des_key("0123456789ABCDEF")
        assert len(key) == 8


class TestPKCS7Padding:
    def test_pad_adds_bytes_to_reach_block_size(self):
        padded = _pad_plaintext_des(b"HELLO")
        assert len(padded) % 8 == 0

    def test_pad_full_block_adds_full_block(self):
        # 8 bytes input → adds 8 bytes of padding (PKCS7 rule)
        padded = _pad_plaintext_des(b"ABCDEFGH")
        assert len(padded) == 16

    def test_unpad_reverses_pad(self):
        original = b"HELLO WORLD"
        assert _unpad_plaintext_des(_pad_plaintext_des(original)) == original

    def test_unpad_invalid_padding_raises(self):
        with pytest.raises(ValueError):
            _unpad_plaintext_des(b"ABCDEFG\x09")  # claims 9 bytes padding, impossible


class TestEncryptDecrypt:
    KEY = "0123456789abcdef"

    def test_basic_round_trip(self):
        ct = encrypt("HELLOWORLD", self.KEY)
        assert decrypt(ct, self.KEY) == "HELLOWORLD"

    def test_ciphertext_is_hex_string(self):
        ct = encrypt("TEST", self.KEY)
        bytes.fromhex(ct)  # raises if not valid hex

    def test_ciphertext_differs_from_plaintext(self):
        ct = encrypt("HELLO", self.KEY)
        assert ct != "HELLO"

    def test_different_keys_give_different_ciphertext(self):
        ct1 = encrypt("HELLO", "0123456789abcdef")
        ct2 = encrypt("HELLO", "fedcba9876543210")
        assert ct1 != ct2

    def test_same_key_same_ciphertext(self):
        ct1 = encrypt("HELLO", self.KEY)
        ct2 = encrypt("HELLO", self.KEY)
        assert ct1 == ct2

    def test_invalid_key_length_raises(self):
        with pytest.raises(ValueError):
            encrypt("HELLO", "short")

    def test_invalid_ciphertext_hex_raises(self):
        with pytest.raises(ValueError):
            decrypt("not_hex_xyz", self.KEY)

    def test_preserves_spaces_and_case(self):
        msg = "Hello World 123"
        ct = encrypt(msg, self.KEY)
        assert decrypt(ct, self.KEY) == msg

    def test_long_message_round_trip(self):
        msg = "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG"
        ct = encrypt(msg, self.KEY)
        assert decrypt(ct, self.KEY) == msg

    def test_ciphertext_length_is_multiple_of_16(self):
        # Each DES block = 8 bytes = 16 hex chars
        ct = encrypt("HELLO", self.KEY)
        assert len(ct) % 16 == 0


class TestGetKeyInfo:
    def test_contains_key(self):
        info = get_key_info("0123456789abcdef")
        assert "0123456789abcdef" in info

    def test_contains_ecb(self):
        info = get_key_info("0123456789abcdef")
        assert "ECB" in info

    def test_invalid_key_returns_error_string(self):
        info = get_key_info("bad")
        assert "Invalid" in info or "invalid" in info.lower()
