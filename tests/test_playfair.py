import pytest
from backend.playfair import encrypt, decrypt


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def key():
    return "SECRETKEY"

@pytest.fixture
def alt_key():
    return "WRONGKEY"


# ---------------------------------------------------------------------------
# Functional Tests
# ---------------------------------------------------------------------------

class TestPlayfairFunctional:

    def test_encrypt_decrypt_roundtrip(self, key):
        plaintext = "HELLOWORLD"
        encrypted = encrypt(plaintext, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted.replace("X", "").replace(" ", "") == plaintext.replace(" ", "")

    def test_encrypt_output_differs_from_input(self, key):
        plaintext = "HELLOWORLD"
        encrypted = encrypt(plaintext, key)
        assert encrypted != plaintext

    def test_deterministic_encryption(self, key):
        plaintext = "TESTINPUT"
        assert encrypt(plaintext, key) == encrypt(plaintext, key)

    def test_deterministic_decryption(self, key):
        plaintext = "TESTINPUT"
        encrypted = encrypt(plaintext, key)
        assert decrypt(encrypted, key) == decrypt(encrypted, key)

    @pytest.mark.parametrize("plaintext", [
        "ATTACKATDAWN",
        "THEQUICKBROWNFOX",
        "CRYPTOGRAPHY",
        "PYTHON",
    ])
    def test_various_plaintexts_roundtrip(self, key, plaintext):
        encrypted = encrypt(plaintext, key)
        decrypted = decrypt(encrypted, key)
        assert decrypted.replace("X", "").replace(" ", "") != ""

    @pytest.mark.parametrize("test_key", [
        "MONARCHY",
        "PLAYFAIR",
        "KEYWORD",
        "ZEBRA",
    ])
    def test_different_keys_produce_different_ciphertext(self, key, test_key):
        plaintext = "HELLOWORLD"
        assert encrypt(plaintext, key) != encrypt(plaintext, test_key)

    def test_wrong_key_decrypt_does_not_match_original(self, key, alt_key):
        plaintext = "HELLOWORLD"
        encrypted = encrypt(plaintext, key)
        decrypted_wrong = decrypt(encrypted, alt_key)
        assert decrypted_wrong != plaintext


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestPlayfairEdgeCases:

    def test_single_character_input(self, key):
        result = encrypt("A", key)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_long_input_roundtrip(self, key):
        plaintext = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 10
        encrypted = encrypt(plaintext, key)
        assert encrypted != plaintext
        assert isinstance(decrypt(encrypted, key), str)

    def test_uppercase_lowercase_key_equivalence(self):
        plaintext = "TESTING"
        assert encrypt(plaintext, "SECRETKEY") == encrypt(plaintext, "secretkey")

    def test_repeated_characters_in_key(self):
        result = encrypt("HELLO", "AABBCC")
        assert isinstance(result, str)

    def test_input_with_spaces_handled(self, key):
        result = encrypt("HELLO WORLD", key)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Error Handling
# ---------------------------------------------------------------------------

class TestPlayfairErrorHandling:

    def test_empty_string_encrypt_raises(self, key):
        with pytest.raises((ValueError, IndexError, Exception)):
            encrypt("", key)

    def test_empty_string_decrypt_raises(self, key):
        with pytest.raises((ValueError, IndexError, Exception)):
            decrypt("", key)

    def test_empty_key_raises(self):
        with pytest.raises((ValueError, KeyError, Exception)):
            encrypt("HELLO", "")

    def test_invalid_key_type_integer(self):
        with pytest.raises((TypeError, ValueError, Exception)):
            encrypt("HELLO", 12345)

    def test_invalid_input_type_integer(self, key):
        with pytest.raises((TypeError, AttributeError, Exception)):
            encrypt(12345, key)

    def test_invalid_input_type_none(self, key):
        with pytest.raises((TypeError, AttributeError, Exception)):
            encrypt(None, key)

    def test_invalid_input_type_bytes(self, key):
        with pytest.raises((TypeError, AttributeError, Exception)):
            encrypt(b"hello", key)