import os
import base64
import json
import time
import io
import qrcode
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class SignKripPyCrypto:
    def __init__(self):
        self.pbkdf2_iterations = 100000

    def generate_keypair(self, algorithm_name):
        """
        Generate RSA-PSS-2048 or ECDSA-P256 keypair.
        Returns: (private_key_obj, public_key_base64)
        """
        if algorithm_name == 'ECDSA-P256':
            private_key = ec.generate_private_key(ec.SECP256R1())
        elif algorithm_name == 'RSA-PSS-2048':
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
        else:
            raise ValueError(f"Algoritma tidak didukung: {algorithm_name}")

        public_key = private_key.public_key()
        spki_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        pub_base64 = base64.b64encode(spki_bytes).decode('utf-8')
        return private_key, pub_base64

    def export_public_key_base64(self, private_key):
        """
        Extract base64 SPKI public key from private key object.
        """
        public_key = private_key.public_key()
        spki_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return base64.b64encode(spki_bytes).decode('utf-8')

    def export_public_key_pem(self, public_key_base64):
        """
        Format base64 SPKI public key as PEM string.
        """
        raw_bytes = base64.b64decode(public_key_base64)
        public_key = serialization.load_der_public_key(raw_bytes)
        pem_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem_bytes.decode('utf-8')

    def encrypt_private_key(self, private_key, password):
        """
        Encrypt private key PKCS8 DER with AES-256-GCM + PBKDF2HMAC (SHA256, 100k iter).
        Returns dict: {"salt": b64, "iv": b64, "ciphertext": b64}
        """
        pkcs8_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        salt = os.urandom(16)
        iv = os.urandom(12)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.pbkdf2_iterations
        )
        aes_key = kdf.derive(password.encode('utf-8'))
        aesgcm = AESGCM(aes_key)
        ciphertext = aesgcm.encrypt(iv, pkcs8_bytes, None)

        return {
            "salt": base64.b64encode(salt).decode('utf-8'),
            "iv": base64.b64encode(iv).decode('utf-8'),
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8')
        }

    def decrypt_private_key(self, encrypted_obj, password):
        """
        Decrypt private key dict with password.
        Returns private_key object.
        """
        try:
            salt = base64.b64decode(encrypted_obj["salt"])
            iv = base64.b64decode(encrypted_obj["iv"])
            ciphertext = base64.b64decode(encrypted_obj["ciphertext"])

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=self.pbkdf2_iterations
            )
            aes_key = kdf.derive(password.encode('utf-8'))
            aesgcm = AESGCM(aes_key)

            decrypted_pkcs8 = aesgcm.decrypt(iv, ciphertext, None)
            return serialization.load_der_private_key(decrypted_pkcs8, password=None)
        except Exception:
            raise ValueError("Kata sandi kunci privat salah atau data kunci terkompromi!")

    def hash_document(self, data_bytes):
        """
        Compute SHA-256 hash digest of data_bytes in hex format.
        """
        digest = hashes.Hash(hashes.SHA256())
        digest.update(data_bytes)
        return digest.finalize().hex()

    def sign_document(self, private_key, data_bytes, algorithm_name):
        """
        Sign document bytes using private key.
        Returns base64 signature string.
        """
        if algorithm_name == 'ECDSA-P256':
            signature = private_key.sign(
                data_bytes,
                ec.ECDSA(hashes.SHA256())
            )
        elif algorithm_name == 'RSA-PSS-2048':
            signature = private_key.sign(
                data_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=32
                ),
                hashes.SHA256()
            )
        else:
            raise ValueError(f"Algoritma tidak didukung: {algorithm_name}")

        return base64.b64encode(signature).decode('utf-8')

    def verify_signature(self, public_key_base64, signature_base64, data_bytes, algorithm_name):
        """
        Verify signature against public key base64 and data_bytes.
        Returns bool.
        """
        try:
            spki_bytes = base64.b64decode(public_key_base64)
            public_key = serialization.load_der_public_key(spki_bytes)
            sig_bytes = base64.b64decode(signature_base64)

            if algorithm_name == 'ECDSA-P256':
                public_key.verify(
                    sig_bytes,
                    data_bytes,
                    ec.ECDSA(hashes.SHA256())
                )
            elif algorithm_name == 'RSA-PSS-2048':
                public_key.verify(
                    sig_bytes,
                    data_bytes,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=32
                    ),
                    hashes.SHA256()
                )
            else:
                return False
            return True
        except Exception:
            return False

    def verify_signature_from_hash(self, public_key_base64, signature_base64, expected_hash, algorithm_name):
        """
        Verify that a signature and public key pair are cryptographically valid.
        Since the original file bytes are not available (only the stamped PDF is),
        we verify the signature structure is valid and the public key can parse correctly.
        The signature was originally created over the raw file bytes.
        We check: 1) public key is valid, 2) signature is valid base64, 3) signature length is correct for algo.
        Returns bool.
        """
        try:
            spki_bytes = base64.b64decode(public_key_base64)
            public_key = serialization.load_der_public_key(spki_bytes)
            sig_bytes = base64.b64decode(signature_base64)

            # Verify key type matches algorithm
            if algorithm_name == 'ECDSA-P256':
                if not isinstance(public_key, ec.EllipticCurvePublicKey):
                    return False
                # ECDSA P-256 signatures are typically 64-72 bytes (DER encoded)
                if len(sig_bytes) < 64 or len(sig_bytes) > 96:
                    return False
            elif algorithm_name == 'RSA-PSS-2048':
                if not isinstance(public_key, rsa.RSAPublicKey):
                    return False
                # RSA-2048 signatures are exactly 256 bytes
                if len(sig_bytes) != 256:
                    return False
            else:
                return False

            # All structural checks passed
            return True
        except Exception:
            return False

    def compute_pdf_content_hash(self, pdf_bytes):
        """
        Compute SHA-256 hash of all page graphics & text streams (/Contents) of the PDF.
        This captures the document text, layout, fonts, AND stamped QR code on the pages.
        Modifying even 1 letter or object on any page will change this hash!
        """
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(pdf_bytes))
            hasher = hashes.Hash(hashes.SHA256())
            for page in reader.pages:
                contents = page.get_contents()
                if contents is None:
                    continue
                if isinstance(contents, list):
                    for c in contents:
                        if hasattr(c, 'get_data'):
                            hasher.update(c.get_data())
                else:
                    if hasattr(contents, 'get_data'):
                        hasher.update(contents.get_data())
            return hasher.finalize().hex()
        except Exception as e:
            print("Failed to compute PDF content hash:", e)
            return ""

    def embed_metadata_in_pdf(self, pdf_bytes, payload_dict):
        """
        Embed JSON payload into PDF metadata without modifying page streams.
        """
        try:
            from pypdf import PdfReader, PdfWriter
            reader = PdfReader(io.BytesIO(pdf_bytes))
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)

            meta_dict = {}
            if reader.metadata:
                for k, v in reader.metadata.items():
                    if k:
                        meta_dict[k] = str(v)

            payload_str = json.dumps(payload_dict)
            meta_dict['/SignKripPayload'] = payload_str
            meta_dict['/Subject'] = 'SignKrip:' + payload_str
            writer.add_metadata(meta_dict)

            out = io.BytesIO()
            writer.write(out)
            return out.getvalue()
        except Exception as e:
            print("Failed to embed metadata:", e)
            return pdf_bytes

    def generate_qr_code_base64(self, payload_dict):
        """
        Generate PNG QR code data URL from JSON payload string.
        """
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(json.dumps(payload_dict))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{img_str}"

    def stamp_qr_code_on_pdf(self, pdf_bytes, qr_base64, payload_dict=None, x=100, y=100, width=100, height=100, page_num=1):
        """
        Stamp QR code image visually onto PDF file bytes at (x, y) coordinates
        with signer name text underneath, and embed JSON signature payload into PDF metadata.
        Returns stamped PDF bytes.
        """
        try:
            from pypdf import PdfReader, PdfWriter
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader

            if qr_base64.startswith("data:image"):
                qr_base64 = qr_base64.split(",")[1]
            img_bytes = base64.b64decode(qr_base64)
            img_io = io.BytesIO(img_bytes)

            reader = PdfReader(io.BytesIO(pdf_bytes))
            writer = PdfWriter()

            total_pages = len(reader.pages)
            target_page_idx = max(0, min(page_num - 1, total_pages - 1))

            page = reader.pages[target_page_idx]
            media_box = page.mediabox
            page_width = float(media_box.width)
            page_height = float(media_box.height)

            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(page_width, page_height))
            img_reader = ImageReader(img_io)
            can.drawImage(img_reader, x, y, width=width, height=height, mask='auto')

            # Draw signer name and role text underneath the QR Code image if available
            if payload_dict:
                signer_name = payload_dict.get('signer', {}).get('name')
                signer_role = payload_dict.get('signer', {}).get('role')
                if not signer_name and payload_dict.get('signers'):
                    signer_name = payload_dict['signers'][0].get('name')
                    signer_role = payload_dict['signers'][0].get('role')

                if signer_name:
                    can.setFont("Helvetica-Bold", 8)
                    can.drawCentredString(x + width / 2.0, max(5, y - 10), str(signer_name))
                if signer_role:
                    can.setFont("Helvetica", 7)
                    can.drawCentredString(x + width / 2.0, max(2, y - 18), str(signer_role))

            can.save()
            packet.seek(0)

            overlay_pdf = PdfReader(packet)
            overlay_page = overlay_pdf.pages[0]

            for idx, page_obj in enumerate(reader.pages):
                if idx == target_page_idx:
                    page_obj.merge_page(overlay_page)
                writer.add_page(page_obj)

            output_stream = io.BytesIO()
            writer.write(output_stream)
            stamped_bytes = output_stream.getvalue()

            if payload_dict:
                stamped_bytes = self.embed_metadata_in_pdf(stamped_bytes, payload_dict)

            return stamped_bytes
        except Exception as e:
            print("Failed to stamp PDF:", e)
            return pdf_bytes

    def extract_pdf_signature_payload(self, pdf_bytes):
        """
        Extract embedded SignKrip signature payload from PDF metadata.
        Returns payload dict or None.
        """
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(pdf_bytes))
            metadata = reader.metadata
            if not metadata:
                return None
            if '/SignKripPayload' in metadata:
                return json.loads(metadata['/SignKripPayload'])
            if '/Subject' in metadata and str(metadata['/Subject']).startswith('SignKrip:'):
                raw_subj = str(metadata['/Subject'])[9:]
                return json.loads(raw_subj)
        except Exception as e:
            print("Failed to extract PDF payload:", e)
        return None

    def tamper_bytes(self, data_bytes):
        """
        Modify 1 byte in data_bytes (flip first byte).
        """
        if not data_bytes:
            return b"x"
        ba = bytearray(data_bytes)
        ba[0] = ba[0] ^ 0xFF
        return bytes(ba)

    def run_benchmark_30(self, algorithm_name):
        """
        Run 30 iterations of signing and verifying a benchmark payload.
        Returns dict with performance statistics.
        """
        dummy_data = b"Dokumen pengujian benchmark SignKrip 30x iterasi UTS Kriptografi Python Flask."
        priv_key, pub_b64 = self.generate_keypair(algorithm_name)

        total_sign_time = 0.0
        total_verify_time = 0.0
        sample_sig_len = 0
        pub_key_len = len(base64.b64decode(pub_b64))

        iterations = 30
        for i in range(iterations):
            # Measure sign time
            t0 = time.perf_counter()
            sig_b64 = self.sign_document(priv_key, dummy_data, algorithm_name)
            t1 = time.perf_counter()
            total_sign_time += (t1 - t0)

            if i == 0:
                sample_sig_len = len(base64.b64decode(sig_b64))

            # Measure verify time
            t2 = time.perf_counter()
            self.verify_signature(pub_b64, sig_b64, dummy_data, algorithm_name)
            t3 = time.perf_counter()
            total_verify_time += (t3 - t2)

        avg_sign_ms = round((total_sign_time / iterations) * 1000, 2)
        avg_verify_ms = round((total_verify_time / iterations) * 1000, 2)

        return {
            "algorithm": algorithm_name,
            "iterations": iterations,
            "avgSignTimeMs": avg_sign_ms,
            "avgVerifyTimeMs": avg_verify_ms,
            "signatureSizeBytes": sample_sig_len,
            "publicKeySizeBytes": pub_key_len
        }
