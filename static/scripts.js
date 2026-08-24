/**
 * app.js
 * Frontend JavaScript for INGRES Kisan Jal-Sahayak.
 * Clean, human-crafted voice assistant (Pi / ElevenLabs inspired) with interactive Voice Orb.
 */

// State Management
let currentLang = 'en'; // 'en' or 'hi'
let autoTTS = true;
let recognition = null;
let isRecording = false;
let finalTranscript = '';
let speechTimeout = null;
let currentPlayingBtn = null;
let currentAudio = null;

// Preset Quick Chips
const QUICK_CHIPS = {
    en: [
        { label: "🌾 Jaipur borewell", query: "Can I drill a borewell in Jaipur?" },
        { label: "💧 Meerut water level", query: "What is the groundwater extraction percentage in Meerut?" },
        { label: "🚜 Crops for Sangrur", query: "Which crop is best to save water in Sangrur Punjab?" },
        { label: "🌽 PMKSY subsidy", query: "What is the subsidy for Drip and Sprinkler under PMKSY?" }
    ],
    hi: [
        { label: "🌾 जयपुर में बोरवेल?", query: "क्या जयपुर में नया बोरवेल लगा सकते हैं?" },
        { label: "💧 मेरठ का भूजल स्तर", query: "मेरठ में भूजल स्थिति और दोहन दर क्या है?" },
        { label: "🚜 संगरूर के लिए फसलें", query: "संगरूर पंजाब के डार्क जोन के लिए कम पानी वाली फसलें बताएं" },
        { label: "💡 PMKSY ड्रिप सब्सिडी", query: "ड्रिप और स्प्रिंकलर सिंचाई पर सरकारी सब्सिडी कितनी है?" }
    ]
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initSpeechRecognition();
    renderQuickChips();
    setOrbState('idle');
});

// ============================================================================
// Voice Orb State Manager (Pi / ElevenLabs style) & Abort Controller
// ============================================================================
let activeAbortController = null;
let currentAbortController = null;
let activeLoadingBubbleId = null;
let activeStreamMsgRef = null;

function cancelActiveRequest() {
    if (activeAbortController) {
        try { activeAbortController.abort(); } catch (e) {}
        activeAbortController = null;
    }
    if (currentAbortController) {
        try { currentAbortController.abort(); } catch (e) {}
        currentAbortController = null;
    }
    if ('speechSynthesis' in window) {
        try { window.speechSynthesis.cancel(); } catch (e) {}
    }
    stopAllSpeech();
    if (activeLoadingBubbleId) {
        removeLoadingBubble(activeLoadingBubbleId);
        activeLoadingBubbleId = null;
    }
    if (activeStreamMsgRef && activeStreamMsgRef.contentDiv) {
        const badge = document.createElement('div');
        badge.className = 'mt-2 inline-block px-2 py-0.5 rounded text-[11px] font-medium bg-rose-950/80 text-rose-300 border border-rose-800/40';
        badge.textContent = currentLang === 'hi' ? '⏹️ [जनरेशन रोक दिया गया / Generation stopped]' : '⏹️ [Generation stopped]';
        activeStreamMsgRef.contentDiv.appendChild(badge);
        activeStreamMsgRef = null;
    } else {
        appendBotMessage(
            currentLang === 'hi' ? '⏹️ *[जनरेशन रोक दिया गया / Generation stopped]*' : '⏹️ *[Generation stopped]*',
            '', 'en', false, false, null, null
        );
    }
    setOrbState('idle');
}

function handleRobotTap() {
    if (activeAbortController || currentAbortController) {
        cancelActiveRequest();
    } else if (isRecording) {
        stopVoiceRecognition(true);
    } else {
        startVoiceRecognition();
    }
}

// Drive the CSS state machine on the robot root & Stop button
function setOrbState(state) {
    const orb = document.getElementById('voice-orb');
    const statusText = document.getElementById('orb-status-text');
    const speakingBanner = document.getElementById('speaking-indicator');
    const inputMicBtn = document.getElementById('input-mic-btn');
    const inputMicIcon = document.getElementById('input-mic-icon');
    const sendBtn = document.getElementById('send-btn');
    const sendIcon = document.getElementById('send-icon');

    if (!orb || !statusText) return;

    orb.className = `jsr-robot state-${state}`;

    if (state === 'listening') {
        statusText.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-rose-400 inline-block animate-ping"></span><span class="text-rose-300 font-medium">${currentLang === 'hi' ? '🎙️ सुन रहा हूँ... बोलिए' : '🎙️ Listening to you...'}</span>`;
        if (speakingBanner) speakingBanner.classList.add('hidden');
        if (inputMicBtn) {
            inputMicBtn.className = 'w-8 h-8 rounded-full bg-rose-600 text-white flex items-center justify-center transition flex-shrink-0 cursor-pointer shadow-md animate-pulse';
            inputMicBtn.onclick = toggleVoiceRecognition;
        }
        if (inputMicIcon) inputMicIcon.className = 'fa-solid fa-microphone-lines text-xs';
        if (sendBtn) {
            sendBtn.className = 'w-8 h-8 rounded-full bg-teal-600 hover:bg-teal-500 text-white flex items-center justify-center transition flex-shrink-0 cursor-pointer shadow-md';
            sendBtn.setAttribute('title', 'Send query');
            sendBtn.onclick = handleSend;
        }
        if (sendIcon) sendIcon.className = 'fa-solid fa-arrow-up text-xs sm:text-sm';

    } else if (state === 'speaking') {
        statusText.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-sky-400 inline-block animate-pulse"></span><span class="text-sky-300">${currentLang === 'hi' ? '🔊 जल साथी बोल रहा है...' : '🔊 Jal Sathi is speaking...'}</span>`;
        if (speakingBanner) {
            speakingBanner.classList.remove('hidden');
            speakingBanner.classList.add('flex');
        }
        if (inputMicBtn) {
            inputMicBtn.className = 'w-8 h-8 rounded-full bg-slate-800/80 hover:bg-slate-700 text-teal-400 hover:text-teal-300 flex items-center justify-center transition flex-shrink-0 cursor-pointer';
            inputMicBtn.onclick = toggleVoiceRecognition;
        }
        if (inputMicIcon) inputMicIcon.className = 'fa-solid fa-microphone text-xs';
        if (sendBtn) {
            sendBtn.className = 'w-8 h-8 rounded-full bg-teal-600 hover:bg-teal-500 text-white flex items-center justify-center transition flex-shrink-0 cursor-pointer shadow-md';
            sendBtn.setAttribute('title', 'Send query');
            sendBtn.onclick = handleSend;
        }
        if (sendIcon) sendIcon.className = 'fa-solid fa-arrow-up text-xs sm:text-sm';

    } else if (state === 'thinking') {
        statusText.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-rose-400 inline-block animate-ping"></span><span class="text-rose-300 font-medium cursor-pointer" onclick="cancelActiveRequest()">${currentLang === 'hi' ? '⏹️ रोकें / Stop generating' : '⏹️ Stop generating (Click to stop)'}</span>`;
        if (speakingBanner) speakingBanner.classList.add('hidden');
        if (inputMicBtn) {
            inputMicBtn.className = 'w-8 h-8 rounded-full bg-rose-900/80 hover:bg-rose-800 text-rose-300 flex items-center justify-center transition flex-shrink-0 cursor-pointer shadow-md animate-pulse';
            inputMicBtn.setAttribute('title', 'Tap to stop generation');
            inputMicBtn.onclick = cancelActiveRequest;
        }
        if (inputMicIcon) inputMicIcon.className = 'fa-solid fa-stop text-xs';
        if (sendBtn) {
            sendBtn.className = 'w-8 h-8 rounded-full bg-rose-600 hover:bg-rose-500 text-white flex items-center justify-center transition flex-shrink-0 cursor-pointer shadow-md animate-pulse';
            sendBtn.setAttribute('title', 'Stop generation');
            sendBtn.onclick = cancelActiveRequest;
        }
        if (sendIcon) sendIcon.className = 'fa-solid fa-stop text-xs';

    } else {
        // Idle
        statusText.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-teal-400 inline-block animate-pulse"></span><span>${currentLang === 'hi' ? '🤖 बोलने के लिए टैप करें' : '🤖 Tap to talk with Jal Sathi'}</span>`;
        if (speakingBanner) speakingBanner.classList.add('hidden');
        if (inputMicBtn) {
            inputMicBtn.className = 'w-8 h-8 rounded-full bg-slate-800/80 hover:bg-slate-700 text-teal-400 hover:text-teal-300 flex items-center justify-center transition flex-shrink-0 cursor-pointer';
            inputMicBtn.onclick = toggleVoiceRecognition;
        }
        if (inputMicIcon) inputMicIcon.className = 'fa-solid fa-microphone text-xs';
        if (sendBtn) {
            sendBtn.className = 'w-8 h-8 rounded-full bg-teal-600 hover:bg-teal-500 text-white flex items-center justify-center transition flex-shrink-0 cursor-pointer shadow-md';
            sendBtn.setAttribute('title', 'Send query');
            sendBtn.onclick = handleSend;
        }
        if (sendIcon) sendIcon.className = 'fa-solid fa-arrow-up text-xs sm:text-sm';
    }
}



const SUGGESTIONS_POOL = {
  en: [
    "🌾 Crops for Sangrur dark zone",
    "💧 Patna groundwater depth",
    "🌦️ Weather forecast for Jaipur",
    "🌧️ Will it rain in Delhi today?",
    "🚜 PMKSY drip irrigation subsidy",
    "⚖️ Tamil Nadu borewell NOC rule",
    "🌊 Ghaziabad water level",
    "🌱 Low water crops for Rajasthan",
    "📜 How to apply for CGWA permit",
    "🌡️ Current temperature in Lucknow"
  ],
  hi: [
    "🌾 संगरूर के लिए कम पानी वाली फसलें",
    "💧 पटना में भूजल स्तर कितना है?",
    "🌦️ जयपुर का 7 दिनों का मौसम",
    "🌧️ क्या आज लखनऊ में बारिश होगी?",
    "🚜 पीएमकेएसवाई ड्रिप सब्सिडी नियम",
    "⚖️ बोरवेल लगाने के सरकारी नियम",
    "🌊 गाजियाबाद का वाटर लेवल",
    "🌱 कम सिंचाई में बाजरा की खेती",
    "📜 बोरवेल एनओसी कैसे प्राप्त करें?",
    "🌡️ आज का मौसम कैसा रहेगा?"
  ]
};

let chipRotationTimer = null;
let currentChipIndex = 0;
let isHoveringChips = false;

// Render Quick Question Chips (Auto-rotating pool with hover pause)
function renderQuickChips() {
    const container = document.getElementById('quick-chips-container');
    if (!container) return;

    if (chipRotationTimer) {
        clearInterval(chipRotationTimer);
        chipRotationTimer = null;
    }

    container.onmouseenter = () => { isHoveringChips = true; };
    container.onmouseleave = () => { isHoveringChips = false; };

    currentChipIndex = 0;

    function displayActiveChips() {
        if (isHoveringChips) return;

        container.classList.add('chip-fade-out');
        setTimeout(() => {
            container.innerHTML = '';
            const activePool = SUGGESTIONS_POOL[currentLang] || SUGGESTIONS_POOL.en;
            for (let i = 0; i < 4; i++) {
                const itemIndex = (currentChipIndex + i) % activePool.length;
                const chipText = activePool[itemIndex];

                const btn = document.createElement('button');
                btn.className = 'quick-chip px-3.5 py-1.5 rounded-full text-xs font-normal whitespace-nowrap cursor-pointer transition-all duration-300 hover:scale-105 select-none';
                btn.innerHTML = chipText;
                btn.onclick = () => {
                    stopAllSpeech();
                    const cleanQuery = chipText.replace(/^[\p{Emoji}\u200d\s]+/u, '').trim();
                    const input = document.getElementById('user-input');
                    if (input) input.value = cleanQuery;
                    handleSend();
                };
                container.appendChild(btn);
            }
            container.classList.remove('chip-fade-out');
            container.classList.add('chip-fade-in');
            setTimeout(() => container.classList.remove('chip-fade-in'), 400);

            currentChipIndex = (currentChipIndex + 2) % activePool.length;
        }, 250);
    }

    displayActiveChips();
    chipRotationTimer = setInterval(displayActiveChips, 6000);

    // Update input placeholder
    const input = document.getElementById('user-input');
    if (input) {
        input.placeholder = (currentLang === 'hi') 
            ? 'अपने जिले या फसल के बारे में पूछें...' 
            : 'Ask about your district water level or crops...';
    }
}


// Toggle Language
function setLanguage(lang) {
    currentLang = lang;
    const btnEn = document.getElementById('lang-btn-en');
    const btnHi = document.getElementById('lang-btn-hi');

    if (lang === 'hi') {
        if (btnHi) btnHi.className = 'px-2.5 py-0.5 rounded-full text-xs font-medium bg-teal-600 text-white transition';
        if (btnEn) btnEn.className = 'px-2.5 py-0.5 rounded-full text-xs font-medium text-slate-400 hover:text-white transition';
    } else {
        if (btnEn) btnEn.className = 'px-2.5 py-0.5 rounded-full text-xs font-medium bg-teal-600 text-white transition';
        if (btnHi) btnHi.className = 'px-2.5 py-0.5 rounded-full text-xs font-medium text-slate-400 hover:text-white transition';
    }

    renderQuickChips();

    if (recognition) {
        recognition.lang = (currentLang === 'hi') ? 'hi-IN' : 'en-IN';
    }
    setOrbState('idle');
}

// Auto-TTS Toggle
function toggleAutoTTS() {
    autoTTS = !autoTTS;
    const icon = document.getElementById('tts-icon');
    const btn = document.getElementById('toggle-tts-btn');

    if (autoTTS) {
        if (icon) icon.className = 'fa-solid fa-volume-high text-xs text-teal-400';
        if (btn) btn.setAttribute('title', 'Voice Audio ON');
    } else {
        if (icon) icon.className = 'fa-solid fa-volume-xmark text-xs text-slate-500';
        if (btn) btn.setAttribute('title', 'Voice Audio OFF');
        stopAllSpeech();
    }
}

// ============================================================================
// Native Speech Recognition Engine (Web Speech API + Barge-In)
// ============================================================================
function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        return null;
    }

    try {
        const rec = new SpeechRecognition();
        rec.continuous = true;
        rec.interimResults = true;
        rec.maxAlternatives = 1;
        rec.lang = (currentLang === 'hi') ? 'hi-IN' : 'en-IN';

        rec.onstart = () => {
            isRecording = true;
            finalTranscript = '';
            stopAllSpeech(); // Barge-in: immediately stop bot speech
            setOrbState('listening');
        };

        rec.onspeechstart = () => {
            stopAllSpeech(); // Barge-in
        };

        rec.onresult = (event) => {
            let interim = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript + ' ';
                } else {
                    interim += event.results[i][0].transcript;
                }
            }

            const currentText = (finalTranscript + interim).trim();
            const inputField = document.getElementById('user-input');
            if (inputField && currentText) {
                inputField.value = currentText;
            }

            // Auto-send when silence is detected after speech (1.8s pause)
            if (speechTimeout) clearTimeout(speechTimeout);
            if (currentText.length > 0) {
                speechTimeout = setTimeout(() => {
                    if (isRecording) {
                        stopVoiceRecognition(true);
                    }
                }, 1800);
            }
        };

        rec.onerror = (event) => {
            console.warn("Speech recognition error:", event.error);
            if (event.error === 'not-allowed') {
                alert("Microphone permission denied. Please allow microphone access in your browser address bar.");
            }
            if (event.error !== 'no-speech') {
                stopVoiceRecognition(false);
            }
        };

        rec.onend = () => {
            if (isRecording) {
                stopVoiceRecognition(true);
            }
        };

        return rec;
    } catch (e) {
        console.warn("Error creating SpeechRecognition instance:", e);
        return null;
    }
}

function startVoiceRecognition() {
    stopAllSpeech();

    // Create fresh instance to avoid stale state bugs
    recognition = setupSpeechRecognition();
    if (!recognition) {
        alert("Speech recognition is not supported in this browser. Please use Google Chrome, Microsoft Edge, or Safari.");
        return;
    }

    try {
        recognition.start();
    } catch (e) {
        console.warn("Recognition start failed, retrying:", e);
        try {
            recognition.stop();
        } catch (_) {}
        setTimeout(() => {
            try {
                recognition = setupSpeechRecognition();
                if (recognition) recognition.start();
            } catch (err) {
                console.error("Second attempt failed:", err);
            }
        }, 100);
    }
}

function stopVoiceRecognition(shouldSubmit = true) {
    if (speechTimeout) clearTimeout(speechTimeout);
    isRecording = false;

    if (recognition) {
        try {
            recognition.onend = null;
            recognition.onerror = null;
            recognition.stop();
        } catch (e) {}
        recognition = null;
    }

    setOrbState('idle');

    if (shouldSubmit) {
        const inputField = document.getElementById('user-input');
        if (inputField && inputField.value.trim()) {
            handleSend();
        }
    }
}

function toggleVoiceRecognition() {
    if (isRecording) {
        stopVoiceRecognition(true);
    } else {
        startVoiceRecognition();
    }
}

function initSpeechRecognition() {
    // Check support on startup
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn("Web Speech API is not supported on this browser.");
    }
}

// ============================================================================
// Single Audio Instance Controller (Strictly Backend Edge-TTS Only)
// ============================================================================
function playServerAudio(audioBase64, btnElement = null) {
    // 1. Stop any currently playing audio immediately
    stopAllSpeech();

    if (!audioBase64) {
        setOrbState('idle');
        return;
    }

    try {
        const src = audioBase64.startsWith('data:') ? audioBase64 : `data:audio/mp3;base64,${audioBase64}`;
        currentAudio = new Audio(src);

        if (btnElement) {
            btnElement.innerHTML = '<i class="fa-solid fa-circle-stop text-sm text-rose-400 animate-pulse"></i>';
            btnElement.setAttribute('title', 'Stop speaking');
            btnElement.classList.add('text-rose-400');
            currentPlayingBtn = btnElement;
        }

        // Animate Voice Orb during playback
        currentAudio.onplay = () => {
            setOrbState('speaking');
        };

        currentAudio.onended = () => {
            onSpeechEnded();
        };

        currentAudio.onerror = (err) => {
            console.log("Audio playback error:", err);
            onSpeechEnded();
        };

        currentAudio.play().catch(e => {
            console.log("Audio play error:", e);
            onSpeechEnded();
        });
    } catch (e) {
        console.log("Server audio initialization error:", e);
        onSpeechEnded();
    }
}

function onSpeechEnded() {
    if (currentPlayingBtn) {
        currentPlayingBtn.innerHTML = '<i class="fa-solid fa-volume-high text-xs"></i>';
        currentPlayingBtn.setAttribute('title', 'Listen out loud');
        currentPlayingBtn.classList.remove('text-rose-400');
        currentPlayingBtn = null;
    }
    if (currentAudio) {
        try {
            currentAudio.pause();
            currentAudio.currentTime = 0;
            currentAudio.src = '';
        } catch (e) {}
        currentAudio = null;
    }
    setOrbState(isRecording ? 'listening' : 'idle');
    const speakingBanner = document.getElementById('speaking-indicator');
    if (speakingBanner) speakingBanner.classList.add('hidden');
}

function stopAllSpeech() {
    if (currentAudio) {
        try {
            currentAudio.pause();
            currentAudio.currentTime = 0;
            currentAudio.src = '';
        } catch (e) {}
        currentAudio = null;
    }

    if (currentPlayingBtn) {
        currentPlayingBtn.innerHTML = '<i class="fa-solid fa-volume-high text-xs"></i>';
        currentPlayingBtn.setAttribute('title', 'Listen out loud');
        currentPlayingBtn.classList.remove('text-rose-400');
        currentPlayingBtn = null;
    }

    setOrbState(isRecording ? 'listening' : 'idle');
    const speakingBanner = document.getElementById('speaking-indicator');
    if (speakingBanner) speakingBanner.classList.add('hidden');
}

async function speakText(btnElement, customText = null, customAudio = null) {
    const isSpeaking = (currentAudio && !currentAudio.paused);
    if (isSpeaking && currentPlayingBtn === btnElement) {
        stopAllSpeech();
        return;
    }

    const audioSource = customAudio || (btnElement ? btnElement.getAttribute('data-audio') : null);
    if (audioSource && audioSource.startsWith('data:audio')) {
        playServerAudio(audioSource, btnElement);
        return;
    }

    // Fetch fresh neural audio from /api/tts
    let textToSpeak = customText || (btnElement ? btnElement.getAttribute('data-spoken') : null) || (btnElement ? btnElement.getAttribute('data-content') : null);
    if (!textToSpeak) return;

    setOrbState('thinking');
    try {
        const response = await fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: textToSpeak, language: currentLang })
        });
        if (response.ok) {
            const blob = await response.blob();
            const reader = new FileReader();
            reader.onloadend = () => {
                playServerAudio(reader.result, btnElement);
            };
            reader.readAsDataURL(blob);
        } else {
            setOrbState('idle');
        }
    } catch (e) {
        console.log("TTS fetch error:", e);
        setOrbState('idle');
    }
}

// Global Keyboard Escape listener
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        stopAllSpeech();
        if (isRecording && recognition) {
            try { recognition.stop(); } catch (err) {}
            setOrbState('idle');
        }
    }
});

// ============================================================================
// Send & Chat Rendering
// ============================================================================
function appendStreamingBotMessage() {
    const container = document.getElementById('chat-container');
    const bubble = document.createElement('div');
    bubble.className = 'flex items-start space-x-3 pr-2 sm:pr-6';

    const msgId = 'bot-msg-' + Date.now();
    bubble.innerHTML = `
        <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-teal-500 to-sky-500 flex-shrink-0 flex items-center justify-center shadow-md">
            <i class="fa-solid fa-droplet text-white text-xs"></i>
        </div>
        <div class="glass-card-bot rounded-2xl rounded-tl-sm p-4 text-slate-200 text-sm shadow-md flex-1">
            <div class="flex items-center justify-between mb-2">
                <span class="font-medium text-teal-300 text-xs flex items-center gap-1.5">
                    <span>Jal</span>
                </span>
                <button onclick="speakText(this)" class="speak-msg-btn text-slate-400 hover:text-teal-300 p-1 transition" title="Listen out loud">
                    <i class="fa-solid fa-volume-high text-xs"></i>
                </button>
            </div>
            <div id="${msgId}" class="bot-text-content leading-relaxed"></div>
        </div>
    `;

    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;

    const contentDiv = document.getElementById(msgId);
    const speakBtn = bubble.querySelector('.speak-msg-btn');

    const streamObj = {
        msgId: msgId,
        contentDiv: contentDiv,
        updateContent: (mdText) => {
            contentDiv.innerHTML = parseMarkdown(mdText);
            container.scrollTop = container.scrollHeight;
        },
        finalize: (result) => {
            contentDiv.innerHTML = parseMarkdown(result.response || '');
            if (speakBtn) {
                speakBtn.setAttribute('data-content', result.response || '');
                if (result.spoken_text) speakBtn.setAttribute('data-spoken', result.spoken_text);
                if (result.audio_base64) speakBtn.setAttribute('data-audio', result.audio_base64);
            }
            container.scrollTop = container.scrollHeight;
        },
        speakBtn: speakBtn
    };
    activeStreamMsgRef = streamObj;
    return streamObj;
}

async function handleSend() {
    const input = document.getElementById('user-input');
    const query = input.value.trim();
    if (!query) return;

    if (activeAbortController || currentAbortController) {
        cancelActiveRequest();
    }

    stopAllSpeech();
    appendUserMessage(query);
    input.value = '';

    setOrbState('thinking');
    const loadingBubbleId = appendLoadingBubble();
    activeLoadingBubbleId = loadingBubbleId;
    activeAbortController = new AbortController();
    currentAbortController = activeAbortController;

    try {
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, language: currentLang }),
            signal: activeAbortController.signal
        });


        if (!response.ok) {
            // Fallback to standard /api/chat if streaming fails
            const standardRes = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, language: 'auto' }),
                signal: activeAbortController.signal
            });
            const data = await standardRes.json();
            removeLoadingBubble(loadingBubbleId);
            activeLoadingBubbleId = null;
            activeAbortController = null;

            if (standardRes.ok) {
                appendBotMessage(data.response, data.sql_query_used, data.language, data.cached_from_db, data.auto_cached, data.spoken_text, data.audio_base64);
            } else {
                setOrbState('idle');
                appendBotMessage(`⚠️ Error: ${data.detail || 'Could not process request.'}`, '', 'en', false, false, null, null);
            }
            return;
        }

        removeLoadingBubble(loadingBubbleId);
        activeLoadingBubbleId = null;
        const streamMsg = appendStreamingBotMessage();
        let accumulatedMd = '';
        let finalMetadata = null;

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const parts = buffer.split('\n\n');
            buffer = parts.pop();

            for (const part of parts) {
                const trimmed = part.trim();
                if (trimmed.startsWith('data: ')) {
                    try {
                        const payload = JSON.parse(trimmed.replace('data: ', '').trim());
                        if (payload.token) {
                            accumulatedMd += payload.token;
                            streamMsg.updateContent(accumulatedMd);
                        }
                        if (payload.done && payload.result) {
                            finalMetadata = payload.result;
                        }
                    } catch (err) {}
                }
            }
        }

        activeAbortController = null;

        if (finalMetadata) {
            streamMsg.finalize(finalMetadata);
            if (autoTTS && finalMetadata.audio_base64) {
                playServerAudio(finalMetadata.audio_base64, streamMsg.speakBtn);
            } else {
                setOrbState('idle');
            }
        } else {
            setOrbState('idle');
        }

    } catch (e) {
        activeLoadingBubbleId = null;
        if (e.name === 'AbortError') {
            console.log("Request explicitly aborted by user.");
            setOrbState('idle');
            return;
        }
        activeAbortController = null;
        removeLoadingBubble(loadingBubbleId);
        setOrbState('idle');
        appendBotMessage(`⚠️ Network/Server Error: ${e.message}`, '', 'en', false, false, null, null);
    }
}



// Markdown parser
function parseMarkdown(md) {
    let html = md
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2 class="text-sm font-semibold text-teal-300 mt-2 mb-1">$1</h2>');

    // Bold & Italic
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em class="text-amber-200/90">$1</em>');

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Links (e.g. Source: [INGRES CGWB Portal](http://ingres.iitr.ac.in/))
    html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-teal-400 hover:text-teal-300 underline font-medium inline-flex items-center gap-1"><span>$1</span><i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i></a>');

    // Unordered lists
    html = html.replace(/^\s*[\-\•]\s+(.*$)/gim, '<li class="flex items-start gap-1.5"><span class="text-teal-400 mt-1">•</span><span>$1</span></li>');

    // Paragraphs
    html = html.replace(/\n\n/g, '</p><p class="mt-2">');
    html = html.replace(/\n/g, '<br/>');

    return `<div class="bot-text-content leading-relaxed"><p>${html}</p></div>`;
}

// Append User Bubble
function appendUserMessage(text) {
    const container = document.getElementById('chat-container');
    const bubble = document.createElement('div');
    bubble.className = 'flex items-start justify-end pl-10';
    bubble.innerHTML = `
        <div class="glass-card-user px-4 py-2.5 rounded-2xl rounded-tr-sm text-slate-100 text-sm max-w-lg">
            <p class="leading-relaxed font-normal">${text.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</p>
        </div>
    `;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
}

// Append Loading Bubble
function appendLoadingBubble() {
    const container = document.getElementById('chat-container');
    const id = 'loading-' + Date.now();
    const bubble = document.createElement('div');
    bubble.id = id;
    bubble.className = 'flex items-start space-x-3 pr-8';
    bubble.innerHTML = `
        <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-teal-500 to-sky-500 flex-shrink-0 flex items-center justify-center shadow-md">
            <i class="fa-solid fa-droplet text-white text-xs animate-pulse"></i>
        </div>
        <div class="glass-card-bot rounded-2xl rounded-tl-sm px-4 py-3 text-slate-300 text-xs shadow-md flex items-center space-x-2">
            <div class="w-1.5 h-1.5 rounded-full bg-teal-400 animate-bounce"></div>
            <div class="w-1.5 h-1.5 rounded-full bg-sky-400 animate-bounce" style="animation-delay: 0.2s"></div>
            <div class="w-1.5 h-1.5 rounded-full bg-amber-400 animate-bounce" style="animation-delay: 0.4s"></div>
            <span class="text-slate-400 font-normal ml-1">Consulting CGWB database...</span>
        </div>
    `;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeLoadingBubble(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// Append Bot Bubble
function appendBotMessage(responseMarkdown, sqlQuery, lang, isCached = false, isAutoCached = false, spokenText = null, audioBase64 = null) {
    const container = document.getElementById('chat-container');
    const bubble = document.createElement('div');
    bubble.className = 'flex items-start space-x-3 pr-2 sm:pr-6';

    const safeSql = sqlQuery ? sqlQuery.replace(/</g, "&lt;").replace(/>/g, "&gt;") : '';
    const sqlSection = sqlQuery && sqlQuery !== 'ERROR' && !sqlQuery.startsWith('NONE') ? `
        <div class="mt-2 pt-2 border-t border-white/[0.06]">
            <details class="text-[11px]">
                <summary class="cursor-pointer text-slate-400 hover:text-teal-300 font-normal py-0.5 select-none transition">
                    <span>Inspect CGWB Assessment SQL</span>
                </summary>
                <div class="mt-1.5 p-2 bg-slate-950/90 rounded-lg border border-slate-800 text-teal-300 font-mono text-[10px] overflow-x-auto relative">
                    <pre>${safeSql}</pre>
                </div>
            </details>
        </div>
    ` : '';

    bubble.innerHTML = `
        <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-teal-500 to-sky-500 flex-shrink-0 flex items-center justify-center shadow-md">
            <i class="fa-solid fa-droplet text-white text-xs"></i>
        </div>
        <div class="glass-card-bot rounded-2xl rounded-tl-sm p-4 text-slate-200 text-sm shadow-md flex-1">
            <div class="flex items-center justify-between mb-2">
                <span class="font-medium text-teal-300 text-xs flex items-center gap-1.5">
                    <span>Jal</span>
                </span>
                <button onclick="speakText(this)" class="speak-msg-btn text-slate-400 hover:text-teal-300 p-1 transition" title="Listen out loud">
                    <i class="fa-solid fa-volume-high text-xs"></i>
                </button>
            </div>
            ${parseMarkdown(responseMarkdown)}
            ${sqlSection}
        </div>
    `;

    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;

    const speakBtn = bubble.querySelector('.speak-msg-btn');
    if (speakBtn) {
        speakBtn.setAttribute('data-content', responseMarkdown);
        if (spokenText) {
            speakBtn.setAttribute('data-spoken', spokenText);
        }
        if (audioBase64) {
            speakBtn.setAttribute('data-audio', audioBase64);
        }
        if (autoTTS && audioBase64) {
            playServerAudio(audioBase64, speakBtn);
        } else if (autoTTS) {
            speakText(speakBtn, spokenText || responseMarkdown, null);
        } else {
            setOrbState('idle');
        }
    }
}
