import json
import io
import base64
import datetime
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from crypto_utils import SignKripPyCrypto

app = Flask(__name__)
CORS(app)
crypto = SignKripPyCrypto()

# In-memory signing history storage for the session
signing_history = []


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/generate-key', methods=['POST'])
def generate_key():
    try:
        data = request.get_json() or {}
        algorithm = data.get('algorithm', 'ECDSA-P256')
        password = data.get('password', '')

        if not password or len(password) < 4:
            return jsonify({'success': False, 'message': 'Kata sandi minimal 4 karakter!'}), 400

        private_key, pub_b64 = crypto.generate_keypair(algorithm)
        encrypted_priv = crypto.encrypt_private_key(private_key, password)

        return jsonify({
            'success': True,
            'publicKey': pub_b64,
            'encryptedPrivateKey': encrypted_priv,
            'algorithm': algorithm,
            'message': f'Berhasil menggenerasi kunci {algorithm}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/sign', methods=['POST'])
def sign_document():
    try:
        file = request.files.get('file')

        if not file:
            return jsonify({'success': False, 'message': 'Berkas dokumen belum diunggah!'}), 400

        file_name = file.filename
        ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
        allowed_exts = {'pdf', 'doc', 'docx', 'txt'}

        if ext not in allowed_exts:
            return jsonify({'success': False, 'message': 'Hanya format berkas PDF, Word (.doc/.docx), dan Teks (.txt) yang didukung!'}), 400

        name = request.form.get('name', '').strip()
        role = request.form.get('role', '').strip()
        institution = request.form.get('institution', '').strip()
        password = request.form.get('password', '')
        algorithm = request.form.get('algorithm', 'ECDSA-P256')
        encrypted_priv_raw = request.form.get('encryptedPrivateKey')
        stamp_x = float(request.form.get('stampX', 135))
        stamp_y = float(request.form.get('stampY', 100))
        stamp_page = int(request.form.get('stampPage', 1))

        if not encrypted_priv_raw:
            return jsonify({'success': False, 'message': 'Data kunci privat terenkripsi tidak ditemukan!'}), 400

        encrypted_priv = json.loads(encrypted_priv_raw) if isinstance(encrypted_priv_raw, str) else encrypted_priv_raw
        file_bytes = file.read()
        file_size = len(file_bytes)

        # Decrypt private key
        private_key = crypto.decrypt_private_key(encrypted_priv, password)

        # Compute SHA-256 Hash of original document
        orig_hash_hex = crypto.hash_document(file_bytes)

        # Public key
        pub_b64 = crypto.export_public_key_base64(private_key)
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        is_pdf = file_name.lower().endswith('.pdf')

        if is_pdf:
            # Step 1: Initial payload for visual QR display
            init_payload = {
                'app': 'SignKrip Digital Signature System (Flask)',
                'version': '1.0',
                'fileName': file_name,
                'fileSize': file_size,
                'hash': orig_hash_hex,
                'algorithm': algorithm,
                'signer': {
                    'name': name,
                    'role': role,
                    'institution': institution,
                    'signedAt': timestamp
                }
            }

            # Generate QR Code base64 image URL
            qr_code_url = crypto.generate_qr_code_base64(init_payload)

            # Stamp QR Code image onto PDF without metadata yet
            stamped_bytes = crypto.stamp_qr_code_on_pdf(
                file_bytes, qr_code_url, payload_dict=None,
                x=stamp_x, y=stamp_y, width=100, height=100, page_num=stamp_page
            )

            # Step 2: Compute page content hash of the stamped PDF (includes text, layout, and QR image)
            stamped_content_hash = crypto.compute_pdf_content_hash(stamped_bytes)

            # Step 3: Sign the stamped content hash with private key
            signature_b64 = crypto.sign_document(private_key, stamped_content_hash.encode('utf-8'), algorithm)

            new_signer_entry = {
                'name': name,
                'role': role,
                'institution': institution,
                'signedAt': timestamp,
                'algorithm': algorithm,
                'publicKey': pub_b64,
                'signature': signature_b64
            }

            payload = {
                'app': 'SignKrip Digital Signature System (Flask)',
                'version': '1.0',
                'fileType': 'pdf',
                'fileName': file_name,
                'fileSize': file_size,
                'hash': orig_hash_hex,
                'stampedContentHash': stamped_content_hash,
                'hashAlgorithm': 'SHA-256',
                'signature': signature_b64,
                'algorithm': algorithm,
                'publicKey': pub_b64,
                'signer': {
                    'name': name,
                    'role': role,
                    'institution': institution,
                    'signedAt': timestamp
                },
                'signers': [new_signer_entry]
            }

            # Step 4: Embed full metadata payload into the stamped PDF
            stamped_bytes = crypto.embed_metadata_in_pdf(stamped_bytes, payload)

            # Save to history
            signing_history.insert(0, payload)

            out_io = io.BytesIO(stamped_bytes)
            return send_file(
                out_io,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"signed_{file_name}"
            )
        else:
            # Universal non-PDF file signing (DOCX, TXT, ZIP, XLSX, dll.)
            signature_b64 = crypto.sign_document(private_key, orig_hash_hex.encode('utf-8'), algorithm)

            new_signer_entry = {
                'name': name,
                'role': role,
                'institution': institution,
                'signedAt': timestamp,
                'algorithm': algorithm,
                'publicKey': pub_b64,
                'signature': signature_b64
            }

            init_payload = {
                'app': 'SignKrip Universal Digital Signature System (Flask)',
                'version': '1.0',
                'fileType': 'universal',
                'fileName': file_name,
                'fileSize': file_size,
                'hash': orig_hash_hex,
                'hashAlgorithm': 'SHA-256',
                'signature': signature_b64,
                'algorithm': algorithm,
                'publicKey': pub_b64,
                'signer': {
                    'name': name,
                    'role': role,
                    'institution': institution,
                    'signedAt': timestamp
                },
                'signers': [new_signer_entry]
            }

            qr_code_url = crypto.generate_qr_code_base64(init_payload)
            init_payload['qrCode'] = qr_code_url

            # Save to history
            signing_history.insert(0, init_payload)

            sig_file_bytes = json.dumps(init_payload, indent=2).encode('utf-8')
            out_io = io.BytesIO(sig_file_bytes)
            return send_file(
                out_io,
                mimetype='application/json',
                as_attachment=True,
                download_name=f"{file_name}.signkrip"
            )

    except ValueError as ve:
        return jsonify({'success': False, 'message': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Gagal menandatangani: {str(e)}'}), 500


@app.route('/api/stamp-pdf', methods=['POST'])
def stamp_pdf_route():
    try:
        import io
        file = request.files.get('file')
        qr_code = request.form.get('qrCode', '')
        payload_raw = request.form.get('payload', '')
        x = float(request.form.get('x', 100))
        y = float(request.form.get('y', 100))
        page_num = int(request.form.get('page', 1))

        if not file or not qr_code:
            return jsonify({'success': False, 'message': 'Berkas PDF dan QR Code diperlukan!'}), 400

        payload_dict = json.loads(payload_raw) if payload_raw else None
        pdf_bytes = file.read()
        stamped_bytes = crypto.stamp_qr_code_on_pdf(
            pdf_bytes, qr_code, payload_dict=payload_dict, x=x, y=y, width=100, height=100, page_num=page_num
        )

        out_io = io.BytesIO(stamped_bytes)
        return send_file(
            out_io,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"signed_{file.filename}"
        )
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/verify', methods=['POST'])
def verify_document():
    try:
        doc_file = request.files.get('file')
        sig_file = request.files.get('sigFile')

        if not doc_file and not sig_file:
            return jsonify({'success': False, 'message': 'Berkas yang akan diverifikasi belum diunggah!'}), 400

        sig_payload = None
        doc_bytes = None
        is_pdf_mode = False

        if doc_file:
            doc_bytes = doc_file.read()
            if doc_file.filename.endswith('.signkrip') or doc_file.filename.endswith('.json'):
                try:
                    sig_payload = json.loads(doc_bytes.decode('utf-8'))
                except Exception:
                    pass

        if not sig_payload and sig_file:
            try:
                sig_bytes = sig_file.read()
                sig_payload = json.loads(sig_bytes.decode('utf-8'))
            except Exception:
                pass

        if not sig_payload and doc_bytes and doc_file.filename.lower().endswith('.pdf'):
            sig_payload = crypto.extract_pdf_signature_payload(doc_bytes)
            is_pdf_mode = True

        if not sig_payload:
            return jsonify({
                'success': False,
                'message': 'Data bukti tanda tangan digital (.signkrip atau metadata PDF) tidak ditemukan!'
            }), 400

        expected_hash = sig_payload.get('hash', '')
        stored_content_hash = sig_payload.get('stampedContentHash')
        file_name = sig_payload.get('fileName', doc_file.filename if doc_file else 'dokumen')

        signers_list = sig_payload.get('signers', [])
        if not signers_list:
            signers_list = [{
                'name': sig_payload.get('signer', {}).get('name', 'Penandatangan'),
                'role': sig_payload.get('signer', {}).get('role', '-'),
                'institution': sig_payload.get('signer', {}).get('institution', '-'),
                'signedAt': sig_payload.get('signer', {}).get('signedAt', '-'),
                'algorithm': sig_payload.get('algorithm', 'ECDSA-P256'),
                'publicKey': sig_payload.get('publicKey', ''),
                'signature': sig_payload.get('signature', '')
            }]

        content_intact = True

        if doc_bytes:
            if is_pdf_mode and stored_content_hash:
                current_content_hash = crypto.compute_pdf_content_hash(doc_bytes)
                content_intact = (current_content_hash == stored_content_hash)
            elif expected_hash:
                actual_file_hash = crypto.hash_document(doc_bytes)
                content_intact = (actual_file_hash == expected_hash)

        verified_signers = []
        all_signatures_valid = True

        for s in signers_list:
            pub_b64 = s.get('publicKey', '')
            sig_b64 = s.get('signature', '')
            algo = s.get('algorithm', 'ECDSA-P256')

            if is_pdf_mode and stored_content_hash:
                data_to_verify = stored_content_hash.encode('utf-8')
            else:
                data_to_verify = expected_hash.encode('utf-8')

            is_sig_valid = crypto.verify_signature(pub_b64, sig_b64, data_to_verify, algo)

            if not is_sig_valid:
                is_sig_valid = crypto.verify_signature_from_hash(pub_b64, sig_b64, expected_hash, algo)

            if not is_sig_valid:
                all_signatures_valid = False

            verified_signers.append({
                'name': s.get('name', '-'),
                'role': s.get('role', '-'),
                'institution': s.get('institution', '-'),
                'signedAt': s.get('signedAt', '-'),
                'algorithm': algo,
                'valid': is_sig_valid
            })

        overall_valid = content_intact and all_signatures_valid and len(verified_signers) > 0

        return jsonify({
            'success': True,
            'valid': overall_valid,
            'hashMatch': content_intact,
            'allSignaturesValid': all_signatures_valid,
            'expectedHash': stored_content_hash or expected_hash,
            'signer': sig_payload.get('signer', {}),
            'signers': verified_signers,
            'algorithm': sig_payload.get('algorithm', 'ECDSA-P256'),
            'fileName': file_name
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Kesalahan verifikasi: {str(e)}'}), 500


@app.route('/api/benchmark', methods=['POST'])
def run_benchmark():
    try:
        data = request.get_json() or {}
        algorithm = data.get('algorithm', 'ECDSA-P256')

        bench_results = crypto.run_benchmark_30(algorithm)
        return jsonify({
            'success': True,
            'benchmark': bench_results
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/test-tamper', methods=['POST'])
def test_tamper():
    try:
        data = request.get_json() or {}
        algorithm = data.get('algorithm', 'ECDSA-P256')

        priv_key, pub_b64 = crypto.generate_keypair(algorithm)
        orig_bytes = b"Dokumen Asli Rahasia UTS Kriptografi SignKrip"
        sig_b64 = crypto.sign_document(priv_key, orig_bytes, algorithm)

        orig_result = crypto.verify_signature(pub_b64, sig_b64, orig_bytes, algorithm)

        # Tamper 1 byte
        tampered_bytes = crypto.tamper_bytes(orig_bytes)
        tampered_result = crypto.verify_signature(pub_b64, sig_b64, tampered_bytes, algorithm)

        passed = (orig_result is True and tampered_result is False)

        return jsonify({
            'success': True,
            'passed': passed,
            'origResult': orig_result,
            'tamperedResult': tampered_result
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/test-wrong-key', methods=['POST'])
def test_wrong_key():
    try:
        data = request.get_json() or {}
        algorithm = data.get('algorithm', 'ECDSA-P256')

        priv_key_A, pub_b64_A = crypto.generate_keypair(algorithm)
        priv_key_B, pub_b64_B = crypto.generate_keypair(algorithm)

        doc_bytes = b"Dokumen Uji Kunci Publik Salah"
        sig_A = crypto.sign_document(priv_key_A, doc_bytes, algorithm)

        # Verify with Key B (Wrong key)
        wrong_key_result = crypto.verify_signature(pub_b64_B, sig_A, doc_bytes, algorithm)
        passed = (wrong_key_result is False)

        return jsonify({
            'success': True,
            'passed': passed,
            'wrongKeyResult': wrong_key_result
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/test-forged-qr', methods=['POST'])
def test_forged_qr():
    try:
        data = request.get_json() or {}
        algorithm = data.get('algorithm', 'ECDSA-P256')

        priv_key, pub_b64 = crypto.generate_keypair(algorithm)
        doc_bytes = b"Dokumen Uji Pemalsuan Signature Payload QR"
        sig_b64 = crypto.sign_document(priv_key, doc_bytes, algorithm)

        # Forge signature string
        forged_sig = sig_b64[:-4] + "AAAA"
        forged_result = crypto.verify_signature(pub_b64, forged_sig, doc_bytes, algorithm)

        passed = (forged_result is False)

        return jsonify({
            'success': True,
            'passed': passed,
            'forgedResult': forged_result
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/history', methods=['GET', 'DELETE'])
def history_api():
    global signing_history
    if request.method == 'DELETE':
        signing_history = []
        return jsonify({'success': True, 'message': 'Riwayat berhasil dibersihkan.'})

    return jsonify({'success': True, 'history': signing_history})


if __name__ == '__main__':
    print("SignKrip Python Flask Application starting on http://localhost:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=True)
