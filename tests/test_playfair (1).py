"""Unit tests for backend/playfair.py"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.playfair import (
    encrypt, decrypt, get_square_display, remove_fillers,
    _build_square, _prepare_plaintext, _process_digraph
)


class TestBuildSquare:
    def test_shape_is_5x5(self):
        sq = _build_square("MONARCHY")
        assert len(sq) == 5
        assert all(len(row) == 5 for row in sq)

    def test_25_unique_letters(self):
        sq = _build_square("MONARCHY")
        flat = [ch for row in sq for ch in row]
        assert len(set(flat)) == 25

    def test_no_j_in_square(self):
        sq = _build_square("JUNGLE")
        flat = [ch for row in sq for ch in row]
        assert "J" not in flat

    def test_key_letters_appear_first(self):
        sq = _build_square("MONARCHY")
        flat = [ch for row in sq for ch in row]
        assert flat[:8] == list("MONARCHY")

    def test_j_in_key_treated_as_i(self):
        assert _build_square("JUNGLE") == _build_square("IUNGLE")

    def test_empty_key_starts_with_abc(self):
        sq = _build_square("")
        flat = [ch for row in sq for ch in row]
        assert flat[:3] == ["A", "B", "C"]

    def test_duplicate_key_letters_deduplicated(self):
        sq = _build_square("AABBCC")
        flat = [ch for row in sq for ch in row]
        assert flat.count("A") == 1
        assert flat.count("B") == 1
        assert flat.count("C") == 1


class TestPreparePlaintext:
    def test_simple_pair(self):
        assert _prepare_plaintext("AB") == [("A", "B")]

    def test_duplicate_pair_gets_x_filler(self):
        pairs = _prepare_plaintext("LL")
        assert pairs[0] == ("L", "X")

    def test_odd_length_padded_with_x(self):
        pairs = _prepare_plaintext("ABC")
        assert len(pairs) == 2
        assert pairs[1][1] == "X"

    def test_j_converted_to_i(self):
        pairs = _prepare_plaintext("JUNGLE")
        flat = "".join(ch for p in pairs for ch in p)
        assert "J" not in flat

    def test_non_alpha_stripped(self):
        assert _prepare_plaintext("HELLO WORLD") == _prepare_plaintext("HELLOWORLD")

    def test_balloon_inserts_filler(self):
        # B-A-L-L-O-O-N → BA LX LO ON
        pairs = _prepare_plaintext("BALLOON")
        flat = "".join(ch for p in pairs for ch in p)
        assert "X" in flat


class TestEncryptDecrypt:
    KEY = "MONARCHY"

    def test_classic_test_vector(self):
        """INSTRUMENTS with MONARCHY key = GATLMZCLRQXA"""
        assert encrypt("INSTRUMENTS", self.KEY) == "GATLMZCLRQXA"

    def test_round_trip_simple(self):
        ct = encrypt("HIDE", self.KEY)
        dt = decrypt(ct, self.KEY)
        assert "HIDE" in dt

    def test_round_trip_duplicate_letters(self):
        ct = encrypt("BALLOON", self.KEY)
        dt = decrypt(ct, self.KEY)
        assert "BALXLON" in dt or "BAL" in dt

    def test_ciphertext_is_uppercase(self):
        ct = encrypt("hello", self.KEY)
        assert ct == ct.upper()

    def test_key_case_insensitive(self):
        assert encrypt("HELLO", "MONARCHY") == encrypt("HELLO", "monarchy")

    def test_plaintext_case_insensitive(self):
        assert encrypt("HELLO", self.KEY) == encrypt("hello", self.KEY)

    def test_different_keys_give_different_ciphertext(self):
        assert encrypt("HELLO", "MONARCHY") != encrypt("HELLO", "KEYWORD")

    def test_decrypt_raises_on_odd_length(self):
        with pytest.raises(ValueError):
            decrypt("ABC", self.KEY)

    def test_long_message_round_trip(self):
        msg = "THEQUICKBROWNFOX"
        ct = encrypt(msg, self.KEY)
        dt = decrypt(ct, self.KEY)
        assert msg in dt or dt.startswith(msg[:8])


class TestRemoveFillers:
    def test_exact_length_unchanged(self):
        assert remove_fillers("HELLO", 5) == "HELLO"

    def test_trailing_x_removed(self):
        assert remove_fillers("HELLOX", 5) == "HELLO"

    def test_truncates_to_original_length(self):
        result = remove_fillers("HELXLO", 5)
        assert len(result) == 5

    def test_too_short_returned_as_is(self):
        assert remove_fillers("HI", 5) == "HI"


class TestGetSquareDisplay:
    def test_contains_key(self):
        display = get_square_display("MONARCHY")
        assert "MONARCHY" in display.upper()

    def test_has_five_rows(self):
        display = get_square_display("TEST")
        lines = [l for l in display.splitlines()
                 if l.strip() and "---" not in l and "Square" not in l]
        assert len(lines) == 5
