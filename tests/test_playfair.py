"""
Unit tests for backend/playfair.py

Run with:  pytest tests/test_playfair.py -v
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.playfair import encrypt, decrypt, _build_square, _prepare_plaintext, get_square_display


# ---------------------------------------------------------------------------
# Key-square tests
# ---------------------------------------------------------------------------

class TestBuildSquare:
    def test_shape(self):
        sq = _build_square("KEY")
        assert len(sq) == 5
        assert all(len(row) == 5 for row in sq)

    def test_25_unique_letters(self):
        sq = _build_square("MONARCHY")
        flat = [ch for row in sq for ch in row]
        assert len(flat) == 25
        assert len(set(flat)) == 25

    def test_no_j(self):
        sq = _build_square("JUNGLE")
        flat = [ch for row in sq for ch in row]
        assert "J" not in flat

    def test_key_letters_come_first(self):
        sq = _build_square("MONARCHY")
        flat = [ch for row in sq for ch in row]
        # M-O-N-A-R-C-H-Y (deduplicated, J→I) must be the leading chars
        expected_prefix = list("MONARCHY")
        assert flat[:len(expected_prefix)] == expected_prefix

    def test_key_with_j_treated_as_i(self):
        sq_j = _build_square("JUNGLE")
        sq_i = _build_square("IUNGLE")
        assert sq_j == sq_i

    def test_empty_key(self):
        sq = _build_square("")
        flat = [ch for row in sq for ch in row]
        assert flat[:3] == ["A", "B", "C"]


# ---------------------------------------------------------------------------
# Plaintext preparation tests
# ---------------------------------------------------------------------------

class TestPreparePlaintext:
    def test_basic_pair(self):
        assert _prepare_plaintext("AB") == [("A", "B")]

    def test_duplicate_pair_gets_filler(self):
        pairs = _prepare_plaintext("BALLOON")
        # B-A | L-X | L-O | ON
        assert ("L", "X") in pairs or ("L", "Z") in pairs

    def test_odd_length_padded(self):
        pairs = _prepare_plaintext("ABC")
        assert len(pairs) == 2          # AB + CX

    def test_j_converted_to_i(self):
        pairs = _prepare_plaintext("JUNGLE")
        flat = "".join(ch for p in pairs for ch in p)
        assert "J" not in flat

    def test_non_alpha_stripped(self):
        pairs1 = _prepare_plaintext("HELLO WORLD")
        pairs2 = _prepare_plaintext("HELLOWORLD")
        assert pairs1 == pairs2


# ---------------------------------------------------------------------------
# Encrypt / Decrypt round-trip tests
# ---------------------------------------------------------------------------

class TestRoundTrip:
    KEY = "MONARCHY"

    def _round_trip(self, message: str):
        ct = encrypt(message, self.KEY)
        dt = decrypt(ct, self.KEY)
        # Strip trailing filler X (or Z) that padding may have added
        clean_in  = message.upper().replace("J", "I")
        clean_out = dt.rstrip("XZ")
        # The original letters must be a prefix of the decrypted output
        assert clean_out.startswith(clean_in) or clean_in.startswith(clean_out)

    def test_instruments(self):
        """Classic Playfair test vector."""
        ct = encrypt("INSTRUMENTS", self.KEY)
        assert ct == "GATLMZCLRQXA"

    def test_short_word(self):
        self._round_trip("HIDE")

    def test_round_trip_duplicate_letters(self):
        ct = encrypt("BALLOON", self.KEY)
        dt = decrypt(ct, self.KEY)
        # Playfair inserts X between duplicate L's → BALXLOON is correct output
        assert "BALXLOON" in dt

    def test_all_same_row(self):
        # Build square; pick letters from the same row
        from backend.playfair import _build_square
        sq = _build_square(self.KEY)
        row_letters = "".join(sq[0])        # first 5 letters in row-0
        self._round_trip(row_letters[:4])   # 4 letters → 2 digraphs, same row

    def test_all_same_col(self):
        from backend.playfair import _build_square
        sq = _build_square(self.KEY)
        col_letters = "".join(row[0] for row in sq)  # first col
        self._round_trip(col_letters[:4])

    def test_rectangle(self):
        self._round_trip("HELP")

    def test_long_message(self):
        self._round_trip("THEQUICKBROWNFOXJUMPSOVERTHELAZYDOG")

    def test_key_case_insensitive(self):
        ct_upper = encrypt("HELLO", "MONARCHY")
        ct_lower = encrypt("HELLO", "monarchy")
        assert ct_upper == ct_lower

    def test_plaintext_case_insensitive(self):
        ct1 = encrypt("HELLO", self.KEY)
        ct2 = encrypt("hello", self.KEY)
        assert ct1 == ct2

    def test_different_keys_differ(self):
        ct1 = encrypt("HELLO", "MONARCHY")
        ct2 = encrypt("HELLO", "KEYWORD")
        assert ct1 != ct2

    def test_decrypt_raises_on_odd_ciphertext(self):
        with pytest.raises(ValueError):
            decrypt("ABC", self.KEY)   # 3 chars is odd → invalid


# ---------------------------------------------------------------------------
# Display helper
# ---------------------------------------------------------------------------

class TestGetSquareDisplay:
    def test_contains_key(self):
        display = get_square_display("KEYWORD")
        assert "KEYWORD" in display.upper()

    def test_five_rows(self):
        display = get_square_display("TEST")
        lines = [l for l in display.splitlines() if l.strip() and "---" not in l and "Square" not in l]
        assert len(lines) == 5
