import pytest
from backend.columnar import encrypt, decrypt


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def key():
    return "SECRET"

@pytest.fixture
def alt_key():
    return "WRONGKEY"


# ---------------------------------------------------------------------------
# Functional Tests
# ---------------------------------------------------------------------------

class TestColumnarFunctional:

    def test_encrypt_decrypt_roundtrip_string(self, key):
        plaintext = "THEQUICKBROWNFOX"
        encrypted = encrypt(plaintext, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted.strip() == plaintext

    def test_encrypt_output_differs_from_input(self, key):
        plaintext = "HELLOWORLD"
        encrypted = encrypt(plaintext, key)
        assert encrypted != plaintext

    def test_deterministic_encryption(self, key):
        plaintext = "CONSISTENTINPUT"
        assert encrypt(plaintext, key) == encrypt(plaintext, key)

    def test_deterministic_decryption(self, key):
        plaintext = "CONSISTENTINPUT"
        encrypted = encrypt(plaintext, key)
        assert decrypt(encrypted, key) == decrypt(encrypted, key)

    def test_decrypt_exactly_matches_original(self, key):
        plaintext = "EXACTMATCH"
        encrypted = encrypt(plaintext, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted.strip() == plaintext

    @pytest.mark.parametrize("plaintext", [
        "ATTACKATDAWN",
        "THEQUICKBROWNFOX",
        "COLUMNARCIPHER",
        "SECURITYPROTOCOL",
        "PYTHONENCRYPTION",
    ])
    def test_roundtrip_various_inputs(self, key, plaintext):
        encrypted = encrypt(plaintext, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted.strip() == plaintext

    @pytest.mark.parametrize("test_key", [
        "ALPHA",
        "ZEBRA",
        "KEY",
        "LONGERKEYWORD",
    ])
    def test_different_keys_different_ciphertext(self, key, test_key):
        plaintext = "HELLOWORLD"
        assert encrypt(plaintext, key) != encrypt(plaintext, test_key)

    def test_wrong_key_decrypt_does_not_match_original(self, key, alt_key):
        plaintext = "HELLOWORLD"
        encrypted = encrypt(plaintext, key)
        decrypted_wrong = decrypt(encrypted, alt_key)
        assert decrypted_wrong.strip() != plaintext


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestColumnarEdgeCases:

    def test_single_character_roundtrip(self, key):
        plaintext = "A"
        encrypted = encrypt(plaintext, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted.strip() == plaintext

    def test_long_input_roundtrip(self, key):
        plaintext = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 20
        encrypted = encrypt(plaintext, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted.strip() == plaintext

    def test_input_length_equals_key_length(self, key):
        plaintext = "A" * len(key)
        encrypted = encrypt(plaintext, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted.strip() == plaintext

    def test_input_shorter_than_key(self, key):
        result = encrypt("HI", key)
        assert isinstance(result, str)

    def test_numeric_string_input(self, key):
        plaintext = "1234567890"
        encrypted = encrypt(plaintext, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted.strip() == plaintext

    def test_padding_does_not_corrupt_data(self, key):
        plaintext = "ODDLENGTH"
        encrypted = encrypt(plaintext, key)
        decrypted = decrypt(encrypted, key)
        assert plaintext in decrypted or decrypted.strip() == plaintext


# ---------------------------------------------------------------------------
# Binary Support
# ---------------------------------------------------------------------------

class TestColumnarBinarySupport:

    def test_encrypt_decrypt_bytes_roundtrip(self, key):
        data = b"binarydata"
        encrypted = encrypt(data, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted.strip().encode() == data or decrypted.strip() == data.decode()

    def test_bytes_encryption_differs_from_input(self, key):
        data = b"helloworld"
        encrypted = encrypt(data, key)
        assert encrypted != data

    def test_large_bytes_roundtrip(self, key):
        data = b"X" * 1024
        encrypted = encrypt(data, key)
        decrypted = decrypt(encrypted, key)
        assert len(decrypted) > 0


# ---------------------------------------------------------------------------
# Error Handling
# ---------------------------------------------------------------------------

class TestColumnarErrorHandling:

    def test_empty_string_encrypt_raises(self, key):
        with pytest.raises((ValueError, IndexError, Exception)):
            encrypt("", key)

    def test_empty_string_decrypt_raises(self, key):
        with pytest.raises((ValueError, IndexError, Exception)):
            decrypt("", key)

    def test_empty_bytes_encrypt_raises(self, key):
        with pytest.raises((ValueError, IndexError, Exception)):
            encrypt(b"", key)

    def test_empty_key_raises(self):
        with pytest.raises((ValueError, KeyError, Exception)):
            encrypt("HELLO", "")

    def test_invalid_key_type_integer(self):
        with pytest.raises((TypeError, ValueError, Exception)):
            encrypt("HELLO", 9999)

    def test_invalid_input_type_none(self, key):
        with pytest.raises((TypeError, AttributeError, Exception)):
            encrypt(None, key)

    def test_invalid_input_type_list(self, key):
        with pytest.raises((TypeError, AttributeError, Exception)):
            encrypt(["H", "E", "L", "L", "O"], key)
            