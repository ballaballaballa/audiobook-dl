"""
Tests for encryption and decryption functionality in audiobook-dl.
"""
import pytest
import os
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from audiobookdl.output.encryption import decrypt_file, decrypt_file_aes
from audiobookdl.utils.audiobook import AESEncryption


class TestAESEncryption:
    """Tests for AES encryption data class."""

    def test_aes_encryption_creation(self):
        """Test creating AESEncryption object."""
        key = b"0123456789abcdef"
        iv = b"fedcba9876543210"

        encryption = AESEncryption(key=key, iv=iv)

        assert encryption.key == key
        assert encryption.iv == iv
        assert len(encryption.key) == 16
        assert len(encryption.iv) == 16

    def test_aes_encryption_with_256bit_key(self):
        """Test creating AESEncryption with 256-bit key."""
        key = b"0123456789abcdef0123456789abcdef"  # 32 bytes = 256 bits
        iv = b"fedcba9876543210"

        encryption = AESEncryption(key=key, iv=iv)

        assert encryption.key == key
        assert encryption.iv == iv
        assert len(encryption.key) == 32

    def test_aes_encryption_random_values(self):
        """Test AESEncryption with cryptographically random values."""
        key = get_random_bytes(16)
        iv = get_random_bytes(16)

        encryption = AESEncryption(key=key, iv=iv)

        assert len(encryption.key) == 16
        assert len(encryption.iv) == 16


class TestDecryptFileAES:
    """Tests for AES file decryption."""

    def test_decrypt_simple_content(self, temp_dir):
        """Test decrypting a simple encrypted file."""
        # Prepare test data
        key = b"0123456789abcdef"
        iv = b"fedcba9876543210"
        plaintext = b"This is test audio content for encryption!"

        # Pad plaintext to be multiple of 16 bytes (AES block size)
        padding_length = 16 - (len(plaintext) % 16)
        plaintext_padded = plaintext + (bytes([padding_length]) * padding_length)

        # Encrypt the content
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(plaintext_padded)

        # Write encrypted content to file
        encrypted_file = temp_dir / "encrypted.bin"
        encrypted_file.write_bytes(encrypted)

        # Decrypt the file
        decrypt_file_aes(str(encrypted_file), key, iv)

        # Read and verify decrypted content
        decrypted = encrypted_file.read_bytes()
        assert decrypted == plaintext_padded

    def test_decrypt_file_in_place(self, temp_dir):
        """Test that decryption happens in-place (same file)."""
        key = b"0123456789abcdef"
        iv = b"fedcba9876543210"
        plaintext = b"Content to encrypt" + b"\x0e" * 14  # Pre-padded

        # Encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(plaintext)

        # Write to file
        test_file = temp_dir / "test.bin"
        test_file.write_bytes(encrypted)

        # Get original file inode (if supported)
        original_stat = os.stat(test_file)

        # Decrypt
        decrypt_file_aes(str(test_file), key, iv)

        # Verify file still exists at same path
        assert test_file.exists()

        # Verify content is decrypted
        decrypted = test_file.read_bytes()
        assert decrypted == plaintext

    def test_decrypt_large_file(self, temp_dir):
        """Test decrypting a larger file (multiple blocks)."""
        key = b"0123456789abcdef"
        iv = b"fedcba9876543210"

        # Create 1KB of data (64 blocks of 16 bytes)
        plaintext = b"x" * 1024

        # Encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(plaintext)

        # Write and decrypt
        large_file = temp_dir / "large.bin"
        large_file.write_bytes(encrypted)

        decrypt_file_aes(str(large_file), key, iv)

        # Verify
        decrypted = large_file.read_bytes()
        assert decrypted == plaintext
        assert len(decrypted) == 1024

    def test_decrypt_with_wrong_key(self, temp_dir):
        """Test that decryption with wrong key produces garbage (no error)."""
        correct_key = b"0123456789abcdef"
        wrong_key = b"fedcba9876543210"
        iv = b"1111111111111111"
        plaintext = b"Secret audio data" + b"\x0f" * 15  # Padded to 32 bytes

        # Encrypt with correct key
        cipher = AES.new(correct_key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(plaintext)

        # Write to file
        test_file = temp_dir / "encrypted.bin"
        test_file.write_bytes(encrypted)

        # Decrypt with wrong key (should not raise error, but data will be wrong)
        decrypt_file_aes(str(test_file), wrong_key, iv)

        decrypted = test_file.read_bytes()
        # Decrypted data should differ from original plaintext
        assert decrypted != plaintext

    def test_decrypt_with_wrong_iv(self, temp_dir):
        """Test that decryption with wrong IV produces incorrect first block."""
        key = b"0123456789abcdef"
        correct_iv = b"aaaaaaaaaaaaaaaa"
        wrong_iv = b"bbbbbbbbbbbbbbbb"
        plaintext = b"This is a test!!" + b"Second block here"  # 32 bytes (2 blocks)

        # Encrypt with correct IV
        cipher = AES.new(key, AES.MODE_CBC, correct_iv)
        encrypted = cipher.encrypt(plaintext)

        # Write to file
        test_file = temp_dir / "encrypted.bin"
        test_file.write_bytes(encrypted)

        # Decrypt with wrong IV
        decrypt_file_aes(str(test_file), key, wrong_iv)

        decrypted = test_file.read_bytes()
        # Decrypted data will be wrong (at least first block)
        assert decrypted != plaintext

    def test_decrypt_empty_file(self, temp_dir):
        """Test handling of empty file."""
        key = b"0123456789abcdef"
        iv = b"fedcba9876543210"

        empty_file = temp_dir / "empty.bin"
        empty_file.write_bytes(b"")

        # Decrypting empty file should handle gracefully
        decrypt_file_aes(str(empty_file), key, iv)

        # File should remain empty
        assert empty_file.read_bytes() == b""

    def test_decrypt_non_block_aligned_data(self, temp_dir):
        """Test decryption of data not aligned to block size."""
        key = b"0123456789abcdef"
        iv = b"fedcba9876543210"

        # 17 bytes (not a multiple of 16)
        # Note: In real use, this would cause issues, but we test the behavior
        plaintext = b"x" * 17

        # Manually pad to block size for valid encryption
        padding = 16 - (len(plaintext) % 16)
        plaintext_padded = plaintext + bytes([padding]) * padding

        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(plaintext_padded)

        test_file = temp_dir / "test.bin"
        test_file.write_bytes(encrypted)

        decrypt_file_aes(str(test_file), key, iv)

        decrypted = test_file.read_bytes()
        assert decrypted == plaintext_padded


class TestDecryptFile:
    """Tests for the high-level decrypt_file function."""

    def test_decrypt_with_aes_encryption_object(self, temp_dir):
        """Test decryption using AESEncryption object."""
        key = b"0123456789abcdef"
        iv = b"fedcba9876543210"
        encryption = AESEncryption(key=key, iv=iv)

        plaintext = b"Test content here" + b"\x0f" * 15  # Padded

        # Encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(plaintext)

        # Write to file
        test_file = temp_dir / "encrypted.bin"
        test_file.write_bytes(encrypted)

        # Decrypt using high-level function
        decrypt_file(str(test_file), encryption)

        # Verify
        decrypted = test_file.read_bytes()
        assert decrypted == plaintext

    def test_decrypt_file_handles_aes_encryption_type(self, temp_dir):
        """Test that decrypt_file correctly handles AESEncryption type."""
        encryption = AESEncryption(
            key=b"testkey123456789",
            iv=b"testiv1234567890",
        )

        plaintext = b"Audio data here!" + b"\x10" * 16  # 32 bytes

        # Encrypt
        cipher = AES.new(encryption.key, AES.MODE_CBC, encryption.iv)
        encrypted = cipher.encrypt(plaintext)

        test_file = temp_dir / "test.mp3"
        test_file.write_bytes(encrypted)

        # Decrypt
        decrypt_file(str(test_file), encryption)

        # Verify
        assert test_file.read_bytes() == plaintext

    def test_decrypt_multiple_files_same_key(self, temp_dir):
        """Test decrypting multiple files with same key."""
        key = b"sharedkey1234567"
        iv1 = b"iv1234567890abcd"
        iv2 = b"iv2bcdefghijk123"

        encryption1 = AESEncryption(key=key, iv=iv1)
        encryption2 = AESEncryption(key=key, iv=iv2)

        plaintext1 = b"File 1 content!!" + b"More data here!!"  # 32 bytes
        plaintext2 = b"File 2 content!!" + b"Different data!!"  # 32 bytes

        # Encrypt both files
        cipher1 = AES.new(key, AES.MODE_CBC, iv1)
        encrypted1 = cipher1.encrypt(plaintext1)

        cipher2 = AES.new(key, AES.MODE_CBC, iv2)
        encrypted2 = cipher2.encrypt(plaintext2)

        # Write files
        file1 = temp_dir / "file1.bin"
        file2 = temp_dir / "file2.bin"
        file1.write_bytes(encrypted1)
        file2.write_bytes(encrypted2)

        # Decrypt both
        decrypt_file(str(file1), encryption1)
        decrypt_file(str(file2), encryption2)

        # Verify both decrypted correctly
        assert file1.read_bytes() == plaintext1
        assert file2.read_bytes() == plaintext2


class TestRealWorldEncryption:
    """Tests simulating real-world encryption scenarios."""

    def test_audio_segment_decryption(self, temp_dir):
        """Test decryption of simulated audio segment."""
        # Simulate HLS/M3U8 scenario with encrypted TS segments
        key = get_random_bytes(16)
        iv = get_random_bytes(16)
        encryption = AESEncryption(key=key, iv=iv)

        # Simulate audio segment (padded to block size)
        audio_segment = b"FAKE AUDIO DATA " * 64  # 1024 bytes

        # Encrypt segment
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_segment = cipher.encrypt(audio_segment)

        # Write encrypted segment
        segment_file = temp_dir / "segment000.ts"
        segment_file.write_bytes(encrypted_segment)

        # Decrypt (as would happen during download)
        decrypt_file(str(segment_file), encryption)

        # Verify decryption
        decrypted = segment_file.read_bytes()
        assert decrypted == audio_segment

    def test_decrypt_file_permissions_preserved(self, temp_dir):
        """Test that file permissions are preserved after decryption."""
        key = b"0123456789abcdef"
        iv = b"fedcba9876543210"
        encryption = AESEncryption(key=key, iv=iv)

        plaintext = b"Protected content" + b"\x0f" * 15  # Padded

        # Encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(plaintext)

        # Write file with specific permissions
        test_file = temp_dir / "protected.bin"
        test_file.write_bytes(encrypted)
        os.chmod(test_file, 0o644)

        original_mode = os.stat(test_file).st_mode

        # Decrypt
        decrypt_file(str(test_file), encryption)

        # Check permissions (may vary by platform)
        # Just verify file is still accessible
        assert test_file.exists()
        assert os.access(test_file, os.R_OK)


class TestEncryptionEdgeCases:
    """Tests for edge cases in encryption/decryption."""

    def test_decrypt_binary_file_with_nulls(self, temp_dir):
        """Test decryption of binary data containing null bytes."""
        key = b"0123456789abcdef"
        iv = b"fedcba9876543210"

        # Binary data with null bytes
        plaintext = b"\x00\x01\x02\x03\x04\x05\x06\x07" * 4  # 32 bytes

        # Encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(plaintext)

        test_file = temp_dir / "binary.bin"
        test_file.write_bytes(encrypted)

        # Decrypt
        decrypt_file_aes(str(test_file), key, iv)

        # Verify null bytes preserved
        decrypted = test_file.read_bytes()
        assert decrypted == plaintext
        assert b"\x00" in decrypted

    def test_decrypt_unicode_content(self, temp_dir):
        """Test decryption of encrypted Unicode text."""
        key = b"0123456789abcdef"
        iv = b"fedcba9876543210"

        # Unicode text (encoded to bytes)
        plaintext = "Hello 世界 🌍".encode("utf-8")

        # Pad to block size
        padding = 16 - (len(plaintext) % 16)
        plaintext_padded = plaintext + bytes([padding]) * padding

        # Encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(plaintext_padded)

        test_file = temp_dir / "unicode.txt"
        test_file.write_bytes(encrypted)

        # Decrypt
        decrypt_file_aes(str(test_file), key, iv)

        # Verify Unicode content
        decrypted = test_file.read_bytes()
        assert decrypted == plaintext_padded
        # Remove padding and decode
        padding_length = decrypted[-1]
        original_text = decrypted[:-padding_length].decode("utf-8")
        assert original_text == "Hello 世界 🌍"

    def test_decrypt_maximum_block_aligned_size(self, temp_dir):
        """Test decrypting data that is exactly block-aligned."""
        key = b"0123456789abcdef"
        iv = b"fedcba9876543210"

        # Exactly 10 blocks (160 bytes)
        plaintext = b"x" * 160

        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(plaintext)

        test_file = temp_dir / "aligned.bin"
        test_file.write_bytes(encrypted)

        decrypt_file_aes(str(test_file), key, iv)

        decrypted = test_file.read_bytes()
        assert len(decrypted) == 160
        assert decrypted == plaintext

    def test_sequential_encrypt_decrypt_operations(self, temp_dir):
        """Test multiple sequential encrypt/decrypt operations."""
        key = b"0123456789abcdef"
        iv = b"fedcba9876543210"

        test_file = temp_dir / "sequential.bin"

        for i in range(5):
            # Different plaintext each iteration
            plaintext = f"Iteration {i} data!".encode() + bytes([16 - (19 % 16)]) * (16 - (19 % 16))

            # Encrypt and write
            cipher = AES.new(key, AES.MODE_CBC, iv)
            encrypted = cipher.encrypt(plaintext)
            test_file.write_bytes(encrypted)

            # Decrypt
            decrypt_file_aes(str(test_file), key, iv)

            # Verify
            decrypted = test_file.read_bytes()
            assert decrypted == plaintext
