(function () {
    'use strict';

    const state = {
        currentPage: 'dashboard',
        publicKeyBase64: null,
        encryptedPrivateKey: null,
        currentAlgorithm: 'ECDSA-P256',
        selectedSignFile: null,
        selectedVerifyDoc: null,
        selectedVerifySigFile: null,
        lastSignedPayload: null,
        signingHistory: []
    };

    document.addEventListener('DOMContentLoaded', () => {
        loadKeysFromStorage();
        loadHistoryFromBackend();
        setupNavigation();
        updateKeyStatusUI();
    });

    // Navigation setup
    function setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const targetPage = item.getAttribute('data-page');
                navigateTo(targetPage);
            });
        });
    }

    window.navigateTo = function (pageId) {
        state.currentPage = pageId;

        document.querySelectorAll('.nav-item').forEach(el => {
            if (el.getAttribute('data-page') === pageId) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        });

        document.querySelectorAll('.page-section').forEach(sec => {
            if (sec.id === `section-${pageId}`) {
                sec.classList.add('active');
            } else {
                sec.classList.remove('active');
            }
        });

        if (pageId === 'sign') {
            // No special action needed
        }

        const titles = {
            dashboard: 'Dashboard Utama',
            generate: 'Pembangkitan Pasangan Kunci',
            sign: 'Tanda Tangan Dokumen',
            verify: 'Verifikasi Keaslian Dokumen',
            testing: 'Pengujian & Benchmark',
            history: 'Riwayat Dokumen Ditandatangani',
            about: 'Tentang Aplikasi SignKrip'
        };
        document.getElementById('current-page-title').textContent = titles[pageId] || 'SignKrip';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    // Toast system
    window.showToast = function (message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span> <span>${message}</span>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(12px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    };

    // LocalStorage & Session
    function loadKeysFromStorage() {
        try {
            const saved = localStorage.getItem('signkrip_flask_keys');
            if (saved) {
                const data = JSON.parse(saved);
                state.publicKeyBase64 = data.publicKey;
                state.encryptedPrivateKey = data.encryptedPrivateKey;
                state.currentAlgorithm = data.algorithm || 'ECDSA-P256';
            }
        } catch (e) { console.error('Failed to load saved keys', e); }
    }

    function saveKeysToStorage() {
        try {
            localStorage.setItem('signkrip_flask_keys', JSON.stringify({
                publicKey: state.publicKeyBase64,
                encryptedPrivateKey: state.encryptedPrivateKey,
                algorithm: state.currentAlgorithm
            }));
        } catch (e) { console.error('Failed to save keys', e); }
    }

    async function loadHistoryFromBackend() {
        try {
            const res = await fetch('/api/history');
            const data = await res.json();
            if (data.success) {
                state.signingHistory = data.history || [];
                renderHistoryTable();
                updateDashboardStats();
            }
        } catch (e) { console.error('Failed to fetch history', e); }
    }

    function updateKeyStatusUI() {
        const indicator = document.getElementById('global-key-indicator');
        const statusText = document.getElementById('global-key-status-text');
        const dashBox = document.getElementById('dash-key-info-box');

        if (state.encryptedPrivateKey && state.publicKeyBase64) {
            indicator.className = 'status-indicator active';
            statusText.textContent = `Kunci Privat: Terisi (${state.currentAlgorithm})`;

            if (dashBox) {
                dashBox.innerHTML = `
                    <div class="alert alert-success">
                        <span>✅ <strong>Kunci Aktif Siap Digunakan!</strong> Algoritma: <code>${state.currentAlgorithm}</code>. Kunci privat terenkripsi aman dengan AES-256-GCM + PBKDF2 di Flask.</span>
                    </div>
                `;
            }
        } else {
            indicator.className = 'status-indicator none';
            statusText.textContent = 'Kunci Privat: Belum Terisi';

            if (dashBox) {
                dashBox.innerHTML = `
                    <div class="alert alert-warning">
                        <span>⚠️ Belum ada pasangan kunci yang dibuat. Silakan buka menu <strong>Generate Kunci</strong> untuk membuat kunci baru.</span>
                    </div>
                `;
            }
        }

        const algoStat = document.getElementById('dash-stat-algo');
        if (algoStat) algoStat.textContent = state.currentAlgorithm;
    }

    function updateDashboardStats() {
        const countEl = document.getElementById('dash-stat-history-count');
        if (countEl) countEl.textContent = state.signingHistory.length;
    }

    // 1. Generate Key Flow
    window.handleGenerateKey = async function (e) {
        e.preventDefault();
        const algo = document.getElementById('gen-algorithm').value;
        const password = document.getElementById('gen-password').value;
        const btn = document.getElementById('btn-gen-key');

        if (!password || password.length < 4) {
            showToast('Kata sandi minimal 4 karakter!', 'warning');
            return;
        }

        btn.disabled = true;
        btn.textContent = '⏳ Memproses Generasi Kunci di Python Flask...';

        try {
            const res = await fetch('/api/generate-key', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ algorithm: algo, password: password })
            });

            const data = await res.json();
            if (!data.success) throw new Error(data.message);

            state.publicKeyBase64 = data.publicKey;
            state.encryptedPrivateKey = data.encryptedPrivateKey;
            state.currentAlgorithm = algo;

            saveKeysToStorage();
            updateKeyStatusUI();

            document.getElementById('gen-public-key-out').textContent = data.publicKey;
            document.getElementById('btn-copy-pubkey').disabled = false;
            document.getElementById('btn-dl-pubkey').disabled = false;

            showToast(data.message, 'success');
        } catch (err) {
            showToast(`Gagal: ${err.message}`, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = '⚡ Generasi Pasangan Kunci (Python Backend)';
        }
    };

    window.copyPublicKey = function () {
        if (!state.publicKeyBase64) return;
        navigator.clipboard.writeText(state.publicKeyBase64).then(() => {
            showToast('Kunci publik disalin ke clipboard!', 'success');
        });
    };

    window.downloadPublicKey = function () {
        if (!state.publicKeyBase64) return;
        const pemContent = `-----BEGIN PUBLIC KEY-----\n${state.publicKeyBase64}\n-----END PUBLIC KEY-----`;
        const blob = new Blob([pemContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `signkrip_flask_${state.currentAlgorithm.toLowerCase()}_public.pub`;
        a.click();
        URL.revokeObjectURL(url);
    };

    // 2. Sign Document Flow
    window.handleSignFileSelect = function (e) {
        const file = e.target.files[0];
        if (!file) return;

        state.selectedSignFile = file;
        document.getElementById('sign-file-name').textContent = file.name;
        document.getElementById('sign-file-size').textContent = `${(file.size / 1024).toFixed(2)} KB`;
        renderPdfPreviewWithQr();
    };

    window.handleSignDocument = async function (e) {
        e.preventDefault();

        if (!state.selectedSignFile) {
            showToast('Pilih berkas terlebih dahulu!', 'warning');
            return;
        }

        const filename = state.selectedSignFile.name.toLowerCase();
        const allowed = ['.pdf', '.doc', '.docx', '.txt'];
        if (!allowed.some(ext => filename.endsWith(ext))) {
            showToast('Hanya berkas PDF, Word (.doc/.docx), dan Teks (.txt) yang didukung!', 'warning');
            return;
        }

        if (!state.encryptedPrivateKey) {
            showToast('Belum ada kunci privat terdaftar! Buka menu Generate Kunci.', 'error');
            return;
        }

        const name = document.getElementById('sign-name').value;
        const role = document.getElementById('sign-role').value;
        const institution = document.getElementById('sign-institution').value;
        const password = document.getElementById('sign-password').value;
        const stampPage = document.getElementById('stamp-page')?.value || 1;
        const stampX = document.getElementById('stamp-x')?.value || 135;
        const stampY = document.getElementById('stamp-y')?.value || 100;
        const btn = document.getElementById('btn-sign-submit');
        const progressBox = document.getElementById('sign-progress-box');
        const resultBox = document.getElementById('sign-result-box');

        btn.disabled = true;
        btn.textContent = '⏳ Memproses Tanda Tangan...';
        if (progressBox) progressBox.style.display = 'block';
        if (resultBox) resultBox.style.display = 'none';

        try {
            const formData = new FormData();
            formData.append('file', state.selectedSignFile);
            formData.append('name', name);
            formData.append('role', role);
            formData.append('institution', institution);
            formData.append('password', password);
            formData.append('algorithm', state.currentAlgorithm);
            formData.append('encryptedPrivateKey', JSON.stringify(state.encryptedPrivateKey));
            formData.append('stampPage', stampPage);
            formData.append('stampX', stampX);
            formData.append('stampY', stampY);

            const res = await fetch('/api/sign', {
                method: 'POST',
                body: formData
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.message || 'Gagal menandatangani dokumen');
            }

            const isPdf = state.selectedSignFile.name.toLowerCase().endsWith('.pdf');
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = isPdf ? `signed_${state.selectedSignFile.name}` : `${state.selectedSignFile.name}.signkrip`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);

            // Show success result
            if (progressBox) progressBox.style.display = 'none';
            if (resultBox) resultBox.style.display = 'block';

            // Refresh history
            loadHistoryFromBackend();
            showToast(isPdf ? '✅ PDF bertanda tangan berhasil diunduh!' : '✅ Bukti tanda tangan digital .signkrip berhasil diunduh!', 'success');
        } catch (err) {
            if (progressBox) progressBox.style.display = 'none';
            showToast(`Gagal menandatangani: ${err.message}`, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = '✍️ Tandatangani & Unduh Berkas Bertanda Tangan';
        }
    };

    window.renderDocumentSheetPlaceholder = function () {
        const canvas = document.getElementById('pdf-preview-canvas');
        if (!canvas) return;

        canvas.width = 380;
        canvas.height = 500;
        const ctx = canvas.getContext('2d');

        // White paper background
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Header Title
        ctx.fillStyle = '#1e293b';
        ctx.font = 'bold 13px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('SURAT PERNYATAAN / DOKUMEN ELEKTRONIK', canvas.width / 2, 40);

        // Green Underline
        ctx.strokeStyle = '#059669';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(35, 48);
        ctx.lineTo(canvas.width - 35, 48);
        ctx.stroke();

        // Sample Content
        ctx.fillStyle = '#475569';
        ctx.font = '9.5px sans-serif';
        ctx.textAlign = 'left';

        const fileName = state.selectedSignFile ? state.selectedSignFile.name : 'Dokumen_Elektronik';
        const lines = [
            `Nama Berkas: ${fileName}`,
            'Saya yang bertanda tangan di bawah ini menyatakan bahwa:',
            'a. Dokumen ini disetujui dan ditandatangani secara digital.',
            'b. Menggunakan skema kriptografi aman (RSA / ECDSA P-256).',
            'c. QR-Code memuat metadata resmi dan digital signature.',
            'd. Perubahan 1 byte pada dokumen akan menolak verifikasi.',
            '',
            'Demikian surat pernyataan dokumen ini dibuat untuk dipergunakan.'
        ];

        let yPos = 78;
        lines.forEach(l => {
            ctx.fillText(l, 30, yPos);
            yPos += 18;
        });

        // Bottom Label
        ctx.fillStyle = '#94a3b8';
        ctx.font = 'italic 8.5px sans-serif';
        ctx.fillText('Stempel Visual Tanda Tangan & QR-Code Digital:', 30, canvas.height - 110);
    };

    window.renderPdfPreviewWithQr = async function () {
        const pageNum = parseInt(document.getElementById('stamp-page')?.value) || 1;
        const x = parseFloat(document.getElementById('stamp-x')?.value) || 135;
        const y = parseFloat(document.getElementById('stamp-y')?.value) || 153;

        const canvas = document.getElementById('pdf-preview-canvas');
        const qrOverlay = document.getElementById('qr-preview-overlay');
        const qrImg = document.getElementById('qr-overlay-img');
        const qrName = document.getElementById('qr-overlay-name');
        const qrRole = document.getElementById('qr-overlay-role');

        if (!canvas) return;

        // Signer info overlay text
        const nameVal = document.getElementById('sign-name')?.value || state.lastSignedPayload?.signer?.name || '';
        const roleVal = document.getElementById('sign-role')?.value || state.lastSignedPayload?.signer?.role || '';

        if (qrName) qrName.textContent = nameVal;
        if (qrRole) qrRole.textContent = roleVal;

        // Dummy QR Code SVG if real QR not created yet
        const dummyQr = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' fill='white'/><rect x='10' y='10' width='30' height='30' fill='black'/><rect x='60' y='10' width='30' height='30' fill='black'/><rect x='10' y='60' width='30' height='30' fill='black'/><rect x='20' y='20' width='10' height='10' fill='white'/><rect x='70' y='20' width='10' height='10' fill='white'/><rect x='20' y='70' width='10' height='10' fill='white'/><rect x='40' y='40' width='20' height='20' fill='black'/></svg>";

        if (qrImg) qrImg.src = state.lastQrCode || dummyQr;
        if (qrOverlay) qrOverlay.style.display = 'block';

        const isPdf = state.selectedSignFile && state.selectedSignFile.name.toLowerCase().endsWith('.pdf');
        const pdfjsLib = window.pdfjsLib;

        if (isPdf && pdfjsLib) {
            try {
                pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
                const arrayBuffer = await state.selectedSignFile.arrayBuffer();
                const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
                const page = await pdf.getPage(Math.min(pageNum, pdf.numPages));

                const viewport = page.getViewport({ scale: 0.5 });
                canvas.width = viewport.width;
                canvas.height = viewport.height;

                const ctx = canvas.getContext('2d');
                await page.render({ canvasContext: ctx, viewport: viewport }).promise;

                const pdfPageHeight = page.view[3] || (viewport.height / 0.5);
                const scale = viewport.width / (page.view[2] || (viewport.width / 0.5));

                const overlayLeft = x * scale;
                const overlayTop = (pdfPageHeight - y - 100) * scale;

                if (qrOverlay) {
                    qrOverlay.style.left = `${Math.max(0, overlayLeft)}px`;
                    qrOverlay.style.top = `${Math.max(0, overlayTop)}px`;
                    qrOverlay.style.width = `${85 * scale}px`;
                }
                return;
            } catch (err) {
                console.error("PDF render failed, fallback to sheet preview:", err);
            }
        }

        // Render document sheet placeholder for non-PDF or initial state
        renderDocumentSheetPlaceholder();

        const scaleX = canvas.width / 595.0;
        const scaleY = canvas.height / 842.0;

        const overlayLeft = x * scaleX;
        const overlayTop = canvas.height - (y * scaleY) - 80;

        if (qrOverlay) {
            qrOverlay.style.left = `${Math.max(10, Math.min(canvas.width - 95, overlayLeft))}px`;
            qrOverlay.style.top = `${Math.max(10, Math.min(canvas.height - 110, overlayTop))}px`;
            qrOverlay.style.width = `85px`;
        }
    };

    window.resetStampPosition = function () {
        document.getElementById('stamp-page').value = 1;
        document.getElementById('stamp-x').value = 135;
        document.getElementById('stamp-y').value = 153;
        renderPdfPreviewWithQr();
    };

    window.downloadSignedPDFDirectly = function () {
        if (!state.lastStampedPdfBase64) {
            downloadStampedPDF();
            return;
        }
        try {
            const byteCharacters = atob(state.lastStampedPdfBase64);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], { type: 'application/pdf' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const originalName = state.selectedSignFile ? state.selectedSignFile.name : 'dokumen.pdf';
            a.download = `signed_${originalName}`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
            showToast('Dokumen PDF ber-tanda tangan & QR Code berhasil diunduh!', 'success');
        } catch (err) {
            showToast(`Gagal mengunduh PDF: ${err.message}`, 'error');
        }
    };

    window.downloadSignaturePayload = function () {
        if (!state.lastSignedPayload) return;
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(state.lastSignedPayload, null, 2));
        const a = document.createElement('a');
        a.setAttribute("href", dataStr);
        a.setAttribute("download", `${state.lastSignedPayload.fileName}.sign.json`);
        document.body.appendChild(a);
        a.click();
        a.remove();
    };

    window.downloadStampedPDF = async function () {
        if (!state.selectedSignFile || !state.lastQrCode) return;
        const btn = document.getElementById('btn-stamp-pdf');
        btn.disabled = true;
        btn.textContent = '⏳ Memproses Stempel PDF...';

        try {
            const formData = new FormData();
            formData.append('file', state.selectedSignFile);
            formData.append('qrCode', state.lastQrCode);
            formData.append('page', document.getElementById('stamp-page').value || 1);
            formData.append('x', document.getElementById('stamp-x').value || 135);
            formData.append('y', document.getElementById('stamp-y').value || 153);
            if (state.lastSignedPayload) {
                formData.append('payload', JSON.stringify(state.lastSignedPayload));
            }

            const res = await fetch('/api/stamp-pdf', {
                method: 'POST',
                body: formData
            });

            if (!res.ok) throw new Error('Gagal menyisipkan QR Code ke PDF');

            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `signed_${state.selectedSignFile.name}`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
            showToast('PDF dengan stempel QR Code berhasil diunduh!', 'success');
        } catch (err) {
            showToast(`Gagal: ${err.message}`, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = '📄 Unduh PDF Ter-Stempel QR Code';
        }
    };

    // 3. Verify Document Flow
    window.handleVerifyDocSelect = function (e) {
        const file = e.target.files[0];
        if (!file) return;
        state.selectedVerifyDoc = file;
        document.getElementById('verify-doc-name').textContent = file.name;
    };

    window.handleVerifySigFileSelect = function (e) {
        const file = e.target.files[0];
        if (!file) return;
        state.selectedVerifySigFile = file;
        const nameEl = document.getElementById('verify-sigfile-name');
        if (nameEl) nameEl.textContent = `Bukti: ${file.name}`;
    };

    window.handleVerifyDocument = async function (e) {
        e.preventDefault();

        if (!state.selectedVerifyDoc && !state.selectedVerifySigFile) {
            showToast('Unggah berkas yang ingin diverifikasi!', 'warning');
            return;
        }

        const btn = document.getElementById('btn-verify-submit');
        btn.disabled = true;
        btn.textContent = '⏳ Memverifikasi Dokumen...';

        try {
            const formData = new FormData();
            if (state.selectedVerifyDoc) formData.append('file', state.selectedVerifyDoc);
            if (state.selectedVerifySigFile) formData.append('sigFile', state.selectedVerifySigFile);

            const res = await fetch('/api/verify', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            if (!data.success) throw new Error(data.message);

            document.getElementById('verify-result-empty').style.display = 'none';
            document.getElementById('verify-result-box').style.display = 'block';

            const banner = document.getElementById('verify-status-banner');
            if (data.valid) {
                banner.className = 'alert alert-success';
                banner.innerHTML = `
                    <div style="font-size: 16px; font-weight: 700; margin-bottom: 4px;">✅ TANDA TANGAN VALID & ASLI</div>
                    <div>Dokumen terbukti otentik 100%. Tanda tangan digital dan integritas berkas terverifikasi valid (tidak ada 1 huruf/byte pun yang diubah).</div>
                `;
            } else {
                banner.className = 'alert alert-error';
                banner.innerHTML = `
                    <div style="font-size: 16px; font-weight: 700; margin-bottom: 4px;">❌ VERIFIKASI GAGAL (TIDAK VALID)</div>
                    <div>${!data.hashMatch ? '• Berkas telah diubah / ditamper dari aslinya!' : ''}
                    ${!data.allSignaturesValid ? '• Tanda tangan digital tidak cocok dengan kunci publik penandatangan!' : ''}</div>
                `;
            }

            document.getElementById('vres-name').textContent = data.signer?.name || '-';
            document.getElementById('vres-role').textContent = `${data.signer?.role || '-'} (${data.signer?.institution || '-'})`;
            document.getElementById('vres-date').textContent = data.signer?.signedAt ? new Date(data.signer.signedAt).toLocaleString('id-ID') : '-';
            document.getElementById('vres-algo').textContent = data.algorithm || '-';
            document.getElementById('vres-hash-match').innerHTML = data.hashMatch
                ? `<span class="badge badge-success">INTACT (Tidak Diubah)</span>`
                : `<span class="badge badge-error">TAMPERED (Telah Diubah)</span>`;

            if (data.valid) {
                showToast('Verifikasi sukses! Dokumen valid & otentik.', 'success');
            } else {
                showToast('Verifikasi gagal! Dokumen diubah atau kunci salah.', 'error');
            }

        } catch (err) {
            showToast(`Kesalahan verifikasi: ${err.message}`, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = '🔍 Verifikasi Keaslian Dokumen';
        }
    };

    // 4. Benchmark & Testing Flow
    window.runBenchmark30 = async function (e) {
        e.preventDefault();
        const btn = document.getElementById('btn-run-benchmark');
        const progressBox = document.getElementById('benchmark-progress-box');
        const statusText = document.getElementById('benchmark-status-text');
        const progressFill = document.getElementById('benchmark-progress-fill');

        btn.disabled = true;
        progressBox.style.display = 'block';
        statusText.textContent = 'Menjalankan 30 iterasi di Python Cryptography Engine...';
        progressFill.style.width = '50%';

        try {
            const algo = state.currentAlgorithm || 'ECDSA-P256';
            const res = await fetch('/api/benchmark', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ algorithm: algo })
            });

            const data = await res.json();
            if (!data.success) throw new Error(data.message);

            progressFill.style.width = '100%';
            const bench = data.benchmark;

            document.getElementById('bench-avg-sign-time').textContent = `${bench.avgSignTimeMs} ms`;
            document.getElementById('bench-avg-verify-time').textContent = `${bench.avgVerifyTimeMs} ms`;
            document.getElementById('bench-sig-size').textContent = `${bench.signatureSizeBytes} B`;
            document.getElementById('bench-pubkey-size').textContent = `${bench.publicKeySizeBytes} B`;

            statusText.textContent = 'Benchmark 30x Iterasi Selesai!';
            showToast(`Benchmark 30x iterasi di Python selesai! Rata-rata Sign: ${bench.avgSignTimeMs}ms`, 'success');
        } catch (err) {
            showToast(`Gagal: ${err.message}`, 'error');
        } finally {
            btn.disabled = false;
        }
    };

    window.runTamperTest = async function (e) {
        e.preventDefault();
        const container = document.getElementById('tamper-test-result');
        container.innerHTML = '⏳ Menjalankan Uji Tamper di Python Backend...';

        try {
            const algo = state.currentAlgorithm || 'ECDSA-P256';
            const res = await fetch('/api/test-tamper', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ algorithm: algo })
            });

            const data = await res.json();
            if (!data.success) throw new Error(data.message);

            const passed = data.passed;
            container.innerHTML = `
                <div class="alert alert-${passed ? 'success' : 'error'}" style="margin-top: 10px;">
                    <div><strong>Status Uji Tamper: ${passed ? 'PASSED ✅' : 'FAILED ❌'}</strong></div>
                    <div style="font-size: 11.5px; margin-top: 4px;">
                        • Dokumen Asli: ${data.origResult ? 'VALID ✓' : 'INVALID ✕'}<br>
                        • Dokumen Ditamper (1 Byte diubah): ${data.tamperedResult ? 'VALID (Error!)' : 'MENOLAK GAGAL ✓ (Sesuai Spesifikasi)'}
                    </div>
                </div>
            `;
            showToast(passed ? 'Uji Tamper PASSED! Python Cryptography berhasil menolak 1-byte tampered file.' : 'FAILED!', passed ? 'success' : 'error');
        } catch (err) {
            container.innerHTML = `<div class="alert alert-error">Error: ${err.message}</div>`;
        }
    };

    window.runWrongKeyTest = async function (e) {
        e.preventDefault();
        const container = document.getElementById('wrongkey-test-result');
        container.innerHTML = '⏳ Menjalankan Uji Kunci Salah di Python Backend...';

        try {
            const algo = state.currentAlgorithm || 'ECDSA-P256';
            const res = await fetch('/api/test-wrong-key', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ algorithm: algo })
            });

            const data = await res.json();
            if (!data.success) throw new Error(data.message);

            const passed = data.passed;
            container.innerHTML = `
                <div class="alert alert-${passed ? 'success' : 'error'}" style="margin-top: 10px;">
                    <div><strong>Status Uji Kunci Salah: ${passed ? 'PASSED ✅' : 'FAILED ❌'}</strong></div>
                    <div style="font-size: 11.5px; margin-top: 4px;">
                        • Verifikasi dengan Kunci Publik B: ${data.wrongKeyResult ? 'VALID (Error!)' : 'MENOLAK GAGAL ✓ (Sesuai Spesifikasi)'}
                    </div>
                </div>
            `;
            showToast(passed ? 'Uji Kunci Salah PASSED! Verifikasi menolak kunci yang tidak cocok.' : 'FAILED!', passed ? 'success' : 'error');
        } catch (err) {
            container.innerHTML = `<div class="alert alert-error">Error: ${err.message}</div>`;
        }
    };

    window.runForgedQRTest = async function (e) {
        e.preventDefault();
        const container = document.getElementById('forgedqr-test-result');
        container.innerHTML = '⏳ Menjalankan Uji QR Code Palsu...';

        try {
            const algo = state.currentAlgorithm || 'ECDSA-P256';
            const res = await fetch('/api/test-forged-qr', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ algorithm: algo })
            });

            const data = await res.json();
            if (!data.success) throw new Error(data.message);

            const passed = data.passed;
            container.innerHTML = `
                <div class="alert alert-${passed ? 'success' : 'error'}" style="margin-top: 10px;">
                    <div><strong>Status Uji QR Palsu: ${passed ? 'PASSED ✅' : 'FAILED ❌'}</strong></div>
                    <div style="font-size: 11.5px; margin-top: 4px;">
                        • Signature Terkompromi: ${data.forgedResult ? 'VALID (Error!)' : 'MENOLAK GAGAL ✓ (QR Terbukti Dipalsukan)'}
                    </div>
                </div>
            `;
            showToast(passed ? 'Uji QR Palsu PASSED! Sistem mendeteksi pemalsuan payload QR.' : 'FAILED!', passed ? 'success' : 'error');
        } catch (err) {
            container.innerHTML = `<div class="alert alert-error">Error: ${err.message}</div>`;
        }
    };

    // 5. History Rendering
    function renderHistoryTable() {
        const tbody = document.getElementById('history-table-body');
        if (!tbody) return;

        if (state.signingHistory.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; color: var(--text-muted); padding: 24px;">Belum ada riwayat dokumen yang ditandatangani.</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = state.signingHistory.map((item, idx) => `
            <tr>
                <td>${idx + 1}</td>
                <td><strong>${item.fileName}</strong></td>
                <td>${item.signer?.name || '-'}</td>
                <td>${item.signer?.role || '-'} (${item.signer?.institution || '-'})</td>
                <td>${item.signer?.signedAt ? new Date(item.signer.signedAt).toLocaleString('id-ID') : '-'}</td>
                <td><span class="badge badge-info">${item.algorithm}</span></td>
                <td>
                    <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 11.5px;" onclick="viewHistoryItem(${idx})">
                        🔍 Detail Metadata
                    </button>
                </td>
            </tr>
        `).join('');
    }

    window.viewHistoryItem = function (idx) {
        const item = state.signingHistory[idx];
        if (!item) return;
        alert(`Penandatangan: ${item.signer?.name || '-'}\nJabatan: ${item.signer?.role || '-'}\nHash SHA-256: ${item.hash}\nSkema: ${item.algorithm}`);
    };

    window.clearHistory = async function () {
        if (confirm('Yakin ingin menghapus seluruh riwayat tanda tangan?')) {
            try {
                await fetch('/api/history', { method: 'DELETE' });
                state.signingHistory = [];
                renderHistoryTable();
                updateDashboardStats();
                showToast('Riwayat berhasil dibersihkan.', 'info');
            } catch (e) {
                showToast('Gagal menghapus riwayat', 'error');
            }
        }
    };

})();
