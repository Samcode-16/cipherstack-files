"""Unit tests for backend/columnar.py"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.columnar import (
    encrypt, decrypt, get_key_order_display,
    _get_column_order, _pad_plaintext
)


class TestGetColumnOrder:
    def test_key_length_matches_order_length(self):
        order = _get_column_order("KEY")
        assert len(order) == 3

    def test_key_example_monarchy(self):
        order = _get_column_order("KEY")
        assert order == [1, 0, 2]

    def test_all_ranks_present(self):
        order = _get_column_order("SECRET")
        assert sorted(order) == list(range(len("SECRET")))

    def test_empty_key_raises(self):
        with pytest.raises(ValueError):
            _get_column_order("")

    def test_single_char_key(self):
        assert _get_column_order("A") == [0]


class TestPadPlaintext:
    def test_already_divisible_no_padding(self):
        result = _pad_plaintext("ABCDEF", 3)
        assert len(result) % 3 == 0
        assert result == "ABCDEF"

    def test_pads_with_x(self):
        result = _pad_plaintext("HELLO", 3)
        assert len(result) % 3 == 0
        assert result.endswith("X")

    def test_strips_non_alpha(self):
        result = _pad_plaintext("HELLO WORLD", 5)
        assert " " not in result

    def test_converts_to_uppercase(self):
        result = _pad_plaintext("hello", 3)
        assert result == result.upper()


class TestEncryptDecrypt:
    KEY = "SECRET"

    def test_basic_round_trip(self):
        ct = encrypt("HELLOWORLD", self.KEY)
        dt = decrypt(ct, self.KEY)
        assert dt.startswith("HELLOWORLD")

    def test_ciphertext_length_equals_padded_length(self):
        plaintext = "HELLO"
        ct = encrypt(plaintext, self.KEY)
        key_len = len(self.KEY)
        padded_len = len(plaintext) + (key_len - len(plaintext) % key_len) % key_len
        assert len(ct) == padded_len

    def test_ciphertext_differs_from_plaintext(self):
        ct = encrypt("HELLOWORLD", self.KEY)
        assert ct != "HELLOWORLD"

    def test_different_keys_give_different_ciphertext(self):
        ct1 = encrypt("HELLOWORLD", "SECRET")
        ct2 = encrypt("HELLOWORLD", "KEYWORD")
        assert ct1 != ct2

    def test_same_key_same_result(self):
        ct1 = encrypt("HELLOWORLD", self.KEY)
        ct2 = encrypt("HELLOWORLD", self.KEY)
        assert ct1 == ct2

    def test_empty_string_returns_empty(self):
        assert encrypt("", self.KEY) == ""
        assert decrypt("", self.KEY) == ""

    def test_decrypt_raises_on_wrong_length(self):
        with pytest.raises(ValueError):
            decrypt("HELLO", "KEY")  # 5 not divisible by 3

    def test_uppercase_output(self):
        ct = encrypt("hello", self.KEY)
        assert ct == ct.upper()

    def test_longer_message(self):
        msg = "THEQUICKBROWNFOXJUMPSOVERTHELAZYDOG"
        ct = encrypt(msg, self.KEY)
        dt = decrypt(ct, self.KEY)
        # J is converted to I per cipher convention
        expected = msg.replace("J", "I")
        assert dt.startswith(expected)

    def test_key_j_treated_as_i(self):
        ct1 = encrypt("HELLO", "JUNGLE")
        ct2 = encrypt("HELLO", "IUNGLE")
        assert ct1 == ct2


class TestGetKeyOrderDisplay:
    def test_contains_key(self):
        display = get_key_order_display("SECRET")
        assert "SECRET" in display

    def test_contains_all_characters(self):
        display = get_key_order_display("KEY")
        for ch in "KEY":
            assert ch in display
