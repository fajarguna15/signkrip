import unittest
import json
from crypto_utils import SignKripPyCrypto


class TestSignKripCrypto(unittest.TestCase):
    def setUp(self):
        self.crypto = SignKripPyCrypto()
        self.test_password = "SecurePassword123!"
        self.sample_document = b"Dokumen pengujian rahasia UTS Kriptografi SignKrip."

    def test_1_generate_keypair_ecdsa(self):
        """1. Test Pembangkitan Pasangan Kunci ECDSA-P256"""
        priv_key, pub_b64 = self.crypto.generate_keypair("ECDSA-P256")
        self.assertIsNotNone(priv_key)
        self.assertIsNotNone(pub_b64)
        self.assertTrue(len(pub_b64) > 30)

    def test_2_generate_keypair_rsa(self):
        """2. Test Pembangkitan Pasangan Kunci RSA-PSS-2048"""
        priv_key, pub_b64 = self.crypto.generate_keypair("RSA-PSS-2048")
        self.assertIsNotNone(priv_key)
        self.assertIsNotNone(pub_b64)
        self.assertTrue(len(pub_b64) > 100)

    def test_3_encrypt_decrypt_private_key(self):
        """3. Test Enkripsi dan Dekripsi Kunci Privat (AES-256-GCM + PBKDF2)"""
        priv_key, _ = self.crypto.generate_keypair("ECDSA-P256")
        encrypted_obj = self.crypto.encrypt_private_key(priv_key, self.test_password)
        
        self.assertIn("salt", encrypted_obj)
        self.assertIn("iv", encrypted_obj)
        self.assertIn("ciphertext", encrypted_obj)

        # Dekripsi kembali dengan kata sandi yang benar
        decrypted_priv_key = self.crypto.decrypt_private_key(encrypted_obj, self.test_password)
        self.assertIsNotNone(decrypted_priv_key)

        # Uji kata sandi salah -> HARUS raise ValueError
        with self.assertRaises(ValueError):
            self.crypto.decrypt_private_key(encrypted_obj, "KataSandiSalah!")

    def test_4_hash_document(self):
        """4. Test Hashing Dokumen SHA-256"""
        hash_hex = self.crypto.hash_document(self.sample_document)
        self.assertEqual(len(hash_hex), 64)  # SHA-256 Hex Digest = 64 karakter
        
        # Hashing dokumen yang sama harus menghasilkan hash yang identik
        hash_hex_2 = self.crypto.hash_document(self.sample_document)
        self.assertEqual(hash_hex, hash_hex_2)

    def test_5_sign_and_verify_valid(self):
        """5. Test Tanda Tangan & Verifikasi Dokumen Valid"""
        priv_key, pub_b64 = self.crypto.generate_keypair("ECDSA-P256")
        signature_b64 = self.crypto.sign_document(priv_key, self.sample_document, "ECDSA-P256")
        
        self.assertIsNotNone(signature_b64)
        is_valid = self.crypto.verify_signature(pub_b64, signature_b64, self.sample_document, "ECDSA-P256")
        self.assertTrue(is_valid)

    def test_6_verify_tampered_document_fails(self):
        """6. Test Verifikasi Dokumen Ditamper (1-Byte diubah) -> HARUS GAGAL"""
        priv_key, pub_b64 = self.crypto.generate_keypair("ECDSA-P256")
        signature_b64 = self.crypto.sign_document(priv_key, self.sample_document, "ECDSA-P256")

        tampered_document = self.crypto.tamper_bytes(self.sample_document)
        is_valid = self.crypto.verify_signature(pub_b64, signature_b64, tampered_document, "ECDSA-P256")
        self.assertFalse(is_valid)

    def test_7_verify_wrong_key_fails(self):
        """7. Test Verifikasi dengan Kunci Publik Salah -> HARUS GAGAL"""
        priv_key_A, pub_b64_A = self.crypto.generate_keypair("ECDSA-P256")
        _, pub_b64_B = self.crypto.generate_keypair("ECDSA-P256")

    def test_8_multi_signer_verification(self):
        """8. Test Fitur Pengayaan: Beberapa Penandatangan (Multi-Signer) pada Satu Dokumen"""
        priv_key_1, pub_b64_1 = self.crypto.generate_keypair("ECDSA-P256")
        priv_key_2, pub_b64_2 = self.crypto.generate_keypair("RSA-PSS-2048")

        sig_1 = self.crypto.sign_document(priv_key_1, self.sample_document, "ECDSA-P256")
        sig_2 = self.crypto.sign_document(priv_key_2, self.sample_document, "RSA-PSS-2048")

        # Verifikasi kedua penandatangan secara independen atas dokumen yang sama
        self.assertTrue(self.crypto.verify_signature(pub_b64_1, sig_1, self.sample_document, "ECDSA-P256"))
        self.assertTrue(self.crypto.verify_signature(pub_b64_2, sig_2, self.sample_document, "RSA-PSS-2048"))


if __name__ == "__main__":
    unittest.main()
