/**
 * UniSchedule Face Verification Engine
 * Uses face-api.js for liveness detection + face matching
 * Runs entirely in browser — no server processing needed
 */

class FaceVerificationEngine {
    constructor(options = {}) {
        this.videoEl    = options.videoEl;
        this.canvasEl   = options.canvasEl;
        this.statusEl   = options.statusEl;
        this.progressEl = options.progressEl;

        this.modelsLoaded  = false;
        this.stream        = null;
        this.profileDescriptor  = null;
        this.verificationInterval = null;

        // Liveness challenges
        this.challenges          = ['blink', 'smile', 'turn_left', 'turn_right'];
        this.currentChallenge    = null;
        this.challengeCompleted  = false;
        this.blinkCount          = 0;
        this.lastEyeState        = 'open';
        this.challengeTimeout    = null;

        // Verification state
        this.livenessVerified = false;
        this.faceMatched      = false;
        this.matchConfidence  = 0;

        // Callbacks
        this.onSuccess  = options.onSuccess  || (() => {});
        this.onFailure  = options.onFailure  || (() => {});
        this.onProgress = options.onProgress || (() => {});
    }

    async loadModels() {
        this.updateStatus('🧠 Loading AI models…', 'loading');
        this.updateProgress(10);
        const MODEL_URL = '/static/face-models';
        await Promise.all([
            faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
            faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
            faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
            faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL),
        ]);
        this.modelsLoaded = true;
        this.updateStatus('✅ AI models loaded', 'success');
        this.updateProgress(25);
    }

    async startCamera() {
        this.updateStatus('📷 Starting camera…', 'loading');
        this.stream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }
        });
        this.videoEl.srcObject = this.stream;
        await new Promise(resolve => this.videoEl.onloadedmetadata = resolve);
        await this.videoEl.play();
        this.canvasEl.width  = this.videoEl.videoWidth;
        this.canvasEl.height = this.videoEl.videoHeight;
        this.updateProgress(40);
    }

    async loadProfilePhoto(photoUrl) {
        this.updateStatus('🔍 Loading your profile photo…', 'loading');
        const img = await faceapi.fetchImage(photoUrl);
        const detection = await faceapi
            .detectSingleFace(img, new faceapi.TinyFaceDetectorOptions())
            .withFaceLandmarks()
            .withFaceDescriptor();
        if (!detection) {
            throw new Error('No face found in profile photo. Please upload a clearer photo.');
        }
        this.profileDescriptor = detection.descriptor;
        this.updateProgress(55);
        this.updateStatus('✅ Profile loaded. Starting liveness check…', 'success');
    }

    startLivenessChallenge() {
        this.currentChallenge   = this.challenges[Math.floor(Math.random() * this.challenges.length)];
        this.challengeCompleted = false;
        this.blinkCount         = 0;
        this.lastEyeState       = 'open';

        const msgs = {
            blink:      '👁️ Please BLINK your eyes twice',
            smile:      '😊 Please SMILE for the camera',
            turn_left:  '👈 Please turn your head slightly LEFT',
            turn_right: '👉 Please turn your head slightly RIGHT',
        };
        const icons = { blink: '👁️', smile: '😊', turn_left: '👈', turn_right: '👉' };
        const hints = {
            blink:      'Close and open your eyes twice',
            smile:      'Show a natural smile',
            turn_left:  'Slowly look to your left',
            turn_right: 'Slowly look to your right',
        };

        this.updateStatus(msgs[this.currentChallenge], 'challenge');
        this.updateProgress(60);

        // Update challenge box if present in DOM
        const box  = document.getElementById('challengeBox');
        const icon = document.getElementById('challengeIcon');
        const txt  = document.getElementById('challengeText');
        const hint = document.getElementById('challengeHint');
        if (box)  box.style.display  = 'block';
        if (icon) icon.textContent   = icons[this.currentChallenge];
        if (txt)  txt.textContent    = msgs[this.currentChallenge];
        if (hint) hint.textContent   = hints[this.currentChallenge];

        this.challengeTimeout = setTimeout(() => {
            if (!this.challengeCompleted) {
                this.updateStatus('⏰ Challenge timed out. Please retry.', 'error');
                this.onFailure('Liveness challenge timed out');
            }
        }, 15000);
    }

    async checkLivenessChallenge(detection) {
        if (this.challengeCompleted) return true;
        const landmarks   = detection.landmarks;
        const expressions = detection.expressions;
        switch (this.currentChallenge) {
            case 'blink':      return this.checkBlink(landmarks);
            case 'smile':      return expressions.happy > 0.7;
            case 'turn_left':  return this.checkHeadTurn(landmarks, 'left');
            case 'turn_right': return this.checkHeadTurn(landmarks, 'right');
        }
        return false;
    }

    checkBlink(landmarks) {
        const leftEye  = landmarks.getLeftEye();
        const rightEye = landmarks.getRightEye();
        const avgEAR   = (this.eyeAspectRatio(leftEye) + this.eyeAspectRatio(rightEye)) / 2;
        const closed   = avgEAR < 0.2;
        if (closed && this.lastEyeState === 'open') {
            this.blinkCount++;
            this.lastEyeState = 'closed';
            this.updateStatus(`👁️ Blink detected! (${this.blinkCount}/2)`, 'challenge');
            const txt = document.getElementById('challengeText');
            if (txt) txt.textContent = `Blink ${this.blinkCount}/2 detected ✓`;
        } else if (!closed && this.lastEyeState === 'closed') {
            this.lastEyeState = 'open';
        }
        return this.blinkCount >= 2;
    }

    eyeAspectRatio(eye) {
        const A = Math.hypot(eye[1].x - eye[5].x, eye[1].y - eye[5].y);
        const B = Math.hypot(eye[2].x - eye[4].x, eye[2].y - eye[4].y);
        const C = Math.hypot(eye[0].x - eye[3].x, eye[0].y - eye[3].y);
        return (A + B) / (2.0 * C);
    }

    checkHeadTurn(landmarks, direction) {
        const nose     = landmarks.getNose();
        const leftEye  = landmarks.getLeftEye();
        const rightEye = landmarks.getRightEye();
        const eyeCX    = (leftEye[0].x + rightEye[3].x) / 2;
        const noseTip  = nose[3];
        const offset   = noseTip.x - eyeCX;
        const faceW    = Math.abs(rightEye[3].x - leftEye[0].x);
        const norm     = offset / faceW;
        if (direction === 'left')  return norm < -0.15;
        if (direction === 'right') return norm >  0.15;
        return false;
    }

    async compareFaces(descriptor) {
        if (!this.profileDescriptor) return { confidence: 0, distance: 1, isMatch: false };
        const distance   = faceapi.euclideanDistance(descriptor, this.profileDescriptor);
        const confidence = Math.max(0, Math.min(100, (1 - distance / 0.6) * 100));
        return { confidence, distance, isMatch: distance < 0.45 };
    }

    async startVerification() {
        this.startLivenessChallenge();
        this.verificationInterval = setInterval(async () => {
            if (this.videoEl.readyState < 2) return;
            const detections = await faceapi
                .detectSingleFace(this.videoEl, new faceapi.TinyFaceDetectorOptions())
                .withFaceLandmarks()
                .withFaceDescriptor()
                .withFaceExpressions();

            const ctx = this.canvasEl.getContext('2d');
            ctx.clearRect(0, 0, this.canvasEl.width, this.canvasEl.height);

            if (!detections) {
                this.updateStatus('👤 No face detected. Position your face in the camera.', 'warning');
                this.drawGuideBox(ctx, false);
                return;
            }

            const resized = faceapi.resizeResults(detections, {
                width: this.canvasEl.width, height: this.canvasEl.height
            });

            if (!this.livenessVerified) {
                this.drawFaceBox(ctx, resized, false);
                const passed = await this.checkLivenessChallenge(detections);
                if (passed) {
                    clearTimeout(this.challengeTimeout);
                    this.challengeCompleted = true;
                    this.livenessVerified   = true;
                    this.updateStatus('✅ Liveness verified! Now matching your face…', 'success');
                    this.updateProgress(75);
                    const box = document.getElementById('challengeBox');
                    if (box) box.style.display = 'none';
                    clearInterval(this.verificationInterval);
                    setTimeout(() => this.doFaceMatching(detections.descriptor), 1000);
                }
            }
        }, 200);
    }

    async doFaceMatching(descriptor) {
        this.updateStatus('🔍 Comparing faces…', 'loading');
        const result = await this.compareFaces(descriptor);
        this.matchConfidence = result.confidence;

        if (result.isMatch) {
            this.faceMatched = true;
            this.updateStatus(`✅ Identity verified! ${result.confidence.toFixed(1)}% match`, 'success');
            this.updateProgress(100);

            // Capture selfie for record
            const snap = document.createElement('canvas');
            snap.width  = this.videoEl.videoWidth;
            snap.height = this.videoEl.videoHeight;
            snap.getContext('2d').drawImage(this.videoEl, 0, 0);
            const selfieData = snap.toDataURL('image/jpeg', 0.8);

            setTimeout(() => {
                this.stopCamera();
                this.onSuccess({ confidence: result.confidence, distance: result.distance, selfie: selfieData });
            }, 1500);
        } else {
            this.updateStatus(`❌ Face does not match. ${result.confidence.toFixed(1)}% confidence. Retrying liveness…`, 'error');
            this.updateProgress(0);
            setTimeout(() => {
                this.livenessVerified = false;
                this.updateProgress(55);
                this.startLivenessChallenge();
                this.startVerification();
            }, 3000);
        }
    }

    drawFaceBox(ctx, detections, isVerified) {
        const box        = detections.detection.box;
        const cornerSize = 20;
        ctx.strokeStyle  = isVerified ? '#00ff00' : '#667eea';
        ctx.lineWidth    = 3;
        ctx.strokeRect(box.x, box.y, box.width, box.height);
        ctx.strokeStyle = isVerified ? '#00ff00' : '#f6ad55';
        ctx.lineWidth   = 4;
        const corners = [
            [box.x, box.y + cornerSize, box.x, box.y, box.x + cornerSize, box.y],
            [box.x + box.width - cornerSize, box.y, box.x + box.width, box.y, box.x + box.width, box.y + cornerSize],
            [box.x, box.y + box.height - cornerSize, box.x, box.y + box.height, box.x + cornerSize, box.y + box.height],
            [box.x + box.width - cornerSize, box.y + box.height, box.x + box.width, box.y + box.height, box.x + box.width, box.y + box.height - cornerSize],
        ];
        corners.forEach(([x1,y1,x2,y2,x3,y3]) => {
            ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2); ctx.lineTo(x3,y3); ctx.stroke();
        });
    }

    drawGuideBox(ctx, faceDetected) {
        const cx = this.canvasEl.width  / 2;
        const cy = this.canvasEl.height / 2;
        const w  = 200, h = 250;
        ctx.strokeStyle = faceDetected ? '#48bb78' : '#fc8181';
        ctx.lineWidth   = 2;
        ctx.setLineDash([10, 5]);
        ctx.strokeRect(cx - w/2, cy - h/2, w, h);
        ctx.setLineDash([]);
    }

    updateStatus(message, type) {
        if (!this.statusEl) return;
        const colors = { loading:'#667eea', success:'#48bb78', error:'#fc8181', warning:'#f6ad55', challenge:'#9f7aea' };
        this.statusEl.textContent = message;
        this.statusEl.style.color = colors[type] || '#ffffff';
    }

    updateProgress(percent) {
        if (!this.progressEl) return;
        this.progressEl.style.width = percent + '%';
        this.onProgress(percent);
    }

    stopCamera() {
        if (this.stream)               { this.stream.getTracks().forEach(t => t.stop()); this.stream = null; }
        if (this.verificationInterval) { clearInterval(this.verificationInterval); }
        if (this.challengeTimeout)     { clearTimeout(this.challengeTimeout); }
    }

    async initialize(profilePhotoUrl) {
        try {
            await this.loadModels();
            await this.startCamera();
            await this.loadProfilePhoto(profilePhotoUrl);
            await this.startVerification();
        } catch (error) {
            this.updateStatus(`❌ Error: ${error.message}`, 'error');
            this.onFailure(error.message);
        }
    }
}
