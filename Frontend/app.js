const startButton =
    document.getElementById("startButton");

const stopButton =
    document.getElementById("stopButton");

const statusElement =
    document.getElementById("agentStatus");

const voiceState =
    document.getElementById("voiceState");

const voiceHint =
    document.getElementById("voiceHint");

const voiceOrb =
    document.getElementById("voiceOrb");

const transcriptElement =
    document.getElementById("transcript");

const emptyTranscript =
    document.getElementById("emptyTranscript");

const messageCountElement =
    document.getElementById("messageCount");

const eventList =
    document.getElementById("eventList");

const connectionPill =
    document.getElementById("connectionPill");

const connectionText =
    document.getElementById("connectionText");

const riskBadge =
    document.getElementById("riskBadge");

const customerValue =
    document.getElementById("customerValue");

const policyValue =
    document.getElementById("policyValue");

const claimTypeValue =
    document.getElementById("claimTypeValue");

const incidentValue =
    document.getElementById("incidentValue");

const coverageValue =
    document.getElementById("coverageValue");

const intentValue =
    document.getElementById("intentValue");

const stepValue =
    document.getElementById("stepValue");

const actionValue =
    document.getElementById("actionValue");

const errorBanner =
    document.getElementById("errorBanner");

const clockElement =
    document.getElementById("clock");


let websocket = null;

let recognition = null;

let callActive = false;

let agentSpeaking = false;

let recognitionStarting = false;

let currentSpeechTranscript = "";

let speechTranscriptSent = false;

let messageCount = 0;


// ============================================================
// CLOCK
// ============================================================

function updateClock() {

    const now =
        new Date();

    clockElement.textContent =
        now.toLocaleTimeString(
            [],
            {
                hour: "2-digit",
                minute: "2-digit",
            }
        );
}


setInterval(
    updateClock,
    1000
);

updateClock();


// ============================================================
// STATUS
// ============================================================

function setVoiceStatus(
    text
) {

    statusElement.textContent =
        text;
}


function setConnection(
    connected
) {

    if (connected) {

        connectionPill.classList.add(
            "live"
        );

        connectionPill.classList.remove(
            "offline"
        );

        connectionText.textContent =
            "Live";

    } else {

        connectionPill.classList.remove(
            "live"
        );

        connectionPill.classList.add(
            "offline"
        );

        connectionText.textContent =
            "Offline";
    }
}


function setOrbState(
    state
) {

    voiceOrb.classList.remove(
        "active",
        "speaking"
    );


    if (state === "listening") {

        voiceOrb.classList.add(
            "active"
        );

        voiceState.textContent =
            "Listening...";

        voiceHint.textContent =
            "Speak naturally";

    } else if (
        state === "speaking"
    ) {

        voiceOrb.classList.add(
            "speaking"
        );

        voiceState.textContent =
            "VoiceClaim is speaking";

        voiceHint.textContent =
            "Processing the response";

    } else if (
        state === "processing"
    ) {

        voiceState.textContent =
            "Thinking...";

        voiceHint.textContent =
            "Checking the claim state";

    } else {

        voiceState.textContent =
            "Ready to receive a claim";

        voiceHint.textContent =
            "Start a call to begin";
    }
}


// ============================================================
// EVENT LOG
// ============================================================

function addEvent(
    text
) {

    const item =
        document.createElement(
            "div"
        );

    item.className =
        "event-item";

    item.innerHTML = `
        <span class="event-dot"></span>
        <span>${escapeHtml(text)}</span>
    `;

    eventList.prepend(
        item
    );

    while (
        eventList.children.length > 12
    ) {

        eventList.removeChild(
            eventList.lastChild
        );
    }
}


function escapeHtml(
    value
) {

    return String(value)
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}


// ============================================================
// TRANSCRIPT
// ============================================================

function createMessage(
    type,
    label
) {

    if (
        emptyTranscript
    ) {

        emptyTranscript.style.display =
            "none";
    }


    const wrapper =
        document.createElement(
            "div"
        );

    wrapper.className =
        type;


    const labelElement =
        document.createElement(
            "div"
        );

    labelElement.className =
        "label";

    labelElement.textContent =
        label;


    const content =
        document.createElement(
            "div"
        );


    wrapper.appendChild(
        labelElement
    );

    wrapper.appendChild(
        content
    );


    transcriptElement.appendChild(
        wrapper
    );


    transcriptElement.scrollTop =
        transcriptElement.scrollHeight;


    return content;
}


function addUserMessage(
    text
) {

    if (
        !text ||
        !text.trim()
    ) {
        return;
    }


    const content =
        createMessage(
            "user",
            "YOU"
        );


    content.textContent =
        text.trim();


    messageCount++;

    updateMessageCount();
}


function addAgentMessage(
    text
) {

    if (
        !text ||
        !text.trim()
    ) {
        return;
    }


    const content =
        createMessage(
            "agent",
            "VOICECLAIM"
        );


    content.textContent =
        text.trim();


    messageCount++;

    updateMessageCount();
}


function updateMessageCount() {

    messageCountElement.textContent =
        `${messageCount} message${messageCount === 1 ? "" : "s"}`;
}


// ============================================================
// LIVE STATE
// ============================================================

function updateAgentState(
    message
) {

    if (
        message.intent
    ) {

        intentValue.textContent =
            humanize(
                message.intent
            );
    }


    if (
        message.next_step
    ) {

        stepValue.textContent =
            humanize(
                message.next_step
            );
    }


    if (
        message.next_step ===
            "request_information"
    ) {

        actionValue.textContent =
            "Collecting information";

    } else if (
        message.next_step ===
            "fact_confirmation"
    ) {

        actionValue.textContent =
            "Awaiting customer confirmation";

    } else if (
        message.next_step ===
            "submission_confirmation"
    ) {

        actionValue.textContent =
            "Awaiting submission confirmation";

    } else if (
        message.next_step ===
            "escalate"
    ) {

        actionValue.textContent =
            "Human review required";

        riskBadge.textContent =
            "HIGH";

    } else {

        actionValue.textContent =
            "Working";
    }
}


function humanize(
    value
) {

    if (!value) {
        return "—";
    }

    return String(value)
        .replaceAll(
            "_",
            " "
        )
        .replace(
            /\b\w/g,
            char => char.toUpperCase()
        );
}


// ============================================================
// SPEECH SYNTHESIS
// ============================================================

function speakAgentResponse(
    text
) {

    if (!text) {

        if (callActive) {
            startRecognition();
        }

        return;
    }


    agentSpeaking =
        true;


    stopRecognition();

    window.speechSynthesis.cancel();


    setOrbState(
        "speaking"
    );


    setVoiceStatus(
        "Speaking"
    );


    const utterance =
        new SpeechSynthesisUtterance(
            text
        );


    utterance.lang =
        "en-IN";


    utterance.rate =
        1.0;


    utterance.pitch =
        1.0;


    utterance.volume =
        1.0;


    utterance.onend =
        () => {

            agentSpeaking =
                false;


            setOrbState(
                "listening"
            );


            setVoiceStatus(
                "Listening"
            );


            if (callActive) {

                setTimeout(
                    startRecognition,
                    150
                );
            }
        };


    utterance.onerror =
        () => {

            agentSpeaking =
                false;


            setOrbState(
                "listening"
            );


            setVoiceStatus(
                "Listening"
            );


            if (callActive) {

                startRecognition();
            }
        };


    window.speechSynthesis.speak(
        utterance
    );
}


// ============================================================
// SPEECH RECOGNITION
// ============================================================

function createRecognition() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;


    if (!SpeechRecognition) {

        showError(
            "Speech recognition is not available. Please use Google Chrome."
        );

        return null;
    }


    const instance =
        new SpeechRecognition();


    instance.lang =
        "en-IN";


    instance.continuous =
        false;


    instance.interimResults =
        true;


    instance.maxAlternatives =
        1;


    instance.onstart =
        () => {

            recognitionStarting =
                false;

            currentSpeechTranscript =
                "";

            speechTranscriptSent =
                false;


            setVoiceStatus(
                "Listening"
            );


            setOrbState(
                "listening"
            );
        };


    instance.onresult =
        (event) => {

            if (agentSpeaking) {
                return;
            }


            let transcript =
                "";


            for (
                let i =
                    event.resultIndex;

                i <
                    event.results.length;

                i++
            ) {

                const result =
                    event.results[i];


                if (
                    result &&
                    result[0]
                ) {

                    transcript +=
                        result[0]
                            .transcript;
                }
            }


            transcript =
                transcript.trim();


            if (!transcript) {
                return;
            }


            currentSpeechTranscript =
                transcript;


            console.log(
                "[VOICE] Recognition:",
                transcript
            );


            const lastResult =
                event.results[
                    event.results.length - 1
                ];


            if (
                lastResult &&
                lastResult.isFinal
            ) {

                sendRecognizedUtterance();
            }
        };


    instance.onerror =
        (event) => {

            console.warn(
                "[VOICE] Recognition error:",
                event.error
            );


            recognitionStarting =
                false;


            if (
                event.error ===
                "not-allowed"
            ) {

                showError(
                    "Microphone permission was denied."
                );

                return;
            }


            if (
                event.error ===
                "no-speech"
            ) {

                if (
                    callActive &&
                    !agentSpeaking
                ) {

                    setTimeout(
                        startRecognition,
                        250
                    );
                }

                return;
            }


            if (
                callActive &&
                !agentSpeaking
            ) {

                setTimeout(
                    startRecognition,
                    400
                );
            }
        };


    instance.onend =
        () => {

            recognitionStarting =
                false;


            if (
                currentSpeechTranscript.trim() &&
                !speechTranscriptSent &&
                !agentSpeaking
            ) {

                sendRecognizedUtterance();
            }


            if (
                callActive &&
                !agentSpeaking
            ) {

                setTimeout(
                    startRecognition,
                    150
                );
            }
        };


    return instance;
}


function startRecognition() {

    if (!callActive) {
        return;
    }


    if (agentSpeaking) {
        return;
    }


    if (recognitionStarting) {
        return;
    }


    if (!recognition) {

        recognition =
            createRecognition();


        if (!recognition) {
            return;
        }
    }


    recognitionStarting =
        true;


    try {

        recognition.start();

    } catch (error) {

        recognitionStarting =
            false;

        console.warn(
            "[VOICE] Recognition start:",
            error
        );


        setTimeout(
            () => {

                if (
                    callActive &&
                    !agentSpeaking
                ) {

                    startRecognition();
                }

            },
            250
        );
    }
}


function stopRecognition() {

    if (!recognition) {
        return;
    }


    try {

        recognition.stop();

    } catch (error) {

        console.warn(
            "[VOICE] Recognition stop:",
            error
        );
    }


    recognitionStarting =
        false;
}


function sendRecognizedUtterance() {

    const transcript =
        currentSpeechTranscript.trim();


    if (!transcript) {
        return;
    }


    if (speechTranscriptSent) {
        return;
    }


    if (agentSpeaking) {
        return;
    }


    if (
        !websocket ||
        websocket.readyState !==
            WebSocket.OPEN
    ) {
        return;
    }


    speechTranscriptSent =
        true;


    addUserMessage(
        transcript
    );


    addEvent(
        `Customer: ${transcript}`
    );


    websocket.send(
        JSON.stringify({
            type:
                "text",

            text:
                transcript,
        })
    );


    setOrbState(
        "processing"
    );


    setVoiceStatus(
        "Processing"
    );


    currentSpeechTranscript =
        "";
}


// ============================================================
// ERROR
// ============================================================

function showError(
    message
) {

    errorBanner.textContent =
        message;

    errorBanner.classList.remove(
        "hidden"
    );


    setTimeout(
        () => {

            errorBanner.classList.add(
                "hidden"
            );

        },
        5000
    );
}


// ============================================================
// WEBSOCKET
// ============================================================

function connectWebSocket() {

const BACKEND_URL =
    "https://voiceclaim-ai-backend.onrender.com";

const WS_URL =
    BACKEND_URL.replace(
        "https://",
        "wss://"
    ) + "/ws/voice";

websocket = new WebSocket(
    WS_URL
);


    websocket.onopen =
        () => {

            callActive =
                true;


            setConnection(
                true
            );


            startButton.disabled =
                true;

            stopButton.disabled =
                false;


            setVoiceStatus(
                "Listening"
            );


            setOrbState(
                "listening"
            );


            addEvent(
                "Voice session connected"
            );


            startRecognition();
        };


    websocket.onmessage =
        (event) => {

            try {

                const message =
                    JSON.parse(
                        event.data
                    );


                switch (
                    message.type
                ) {

                    case "agent_processing":

                        setVoiceStatus(
                            "Processing"
                        );

                        setOrbState(
                            "processing"
                        );

                        actionValue.textContent =
                            "Processing customer input";

                        addEvent(
                            "Agent processing customer message"
                        );

                        break;


                    case "agent_response":

                        addAgentMessage(
                            message.text
                        );


                        updateAgentState(
                            message
                        );


                        addEvent(
                            `Agent response: ${message.text}`
                        );


                        speakAgentResponse(
                            message.text
                        );

                        break;


                    case "error":

                        showError(
                            message.message
                        );


                        addEvent(
                            `ERROR: ${message.message}`
                        );


                        agentSpeaking =
                            false;


                        setOrbState(
                            "idle"
                        );


                        if (
                            callActive
                        ) {

                            startRecognition();
                        }

                        break;


                    case "pong":

                        break;


                    default:

                        console.log(
                            "Unknown message:",
                            message
                        );
                }


            } catch (
                error
            ) {

                console.error(
                    "Frontend message error:",
                    error
                );
            }
        };


    websocket.onerror =
        (error) => {

            console.error(
                "[VOICE] WebSocket error:",
                error
            );


            addEvent(
                "WebSocket connection error"
            );


            setConnection(
                false
            );
        };


    websocket.onclose =
        () => {

            callActive =
                false;


            agentSpeaking =
                false;


            stopRecognition();


            window.speechSynthesis.cancel();


            websocket =
                null;


            startButton.disabled =
                false;

            stopButton.disabled =
                true;


            setConnection(
                false
            );


            setVoiceStatus(
                "Ready"
            );


            setOrbState(
                "idle"
            );


            addEvent(
                "Voice session ended"
            );
        };
}


// ============================================================
// CALL CONTROLS
// ============================================================

function startCall() {

    if (callActive) {
        return;
    }


    const supported =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;


    if (!supported) {

        showError(
            "Please use Google Chrome for the live voice demo."
        );

        return;
    }


    currentSpeechTranscript =
        "";

    speechTranscriptSent =
        false;


    connectWebSocket();
}


function stopCall() {

    callActive =
        false;


    stopRecognition();


    window.speechSynthesis.cancel();


    agentSpeaking =
        false;


    if (
        websocket &&
        websocket.readyState ===
            WebSocket.OPEN
    ) {

        websocket.send(
            JSON.stringify({
                type:
                    "stop",
            })
        );


        websocket.close();
    }


    websocket =
        null;


    startButton.disabled =
        false;


    stopButton.disabled =
        true;


    setConnection(
        false
    );


    setVoiceStatus(
        "Ready"
    );


    setOrbState(
        "idle"
    );


    addEvent(
        "Voice session ended"
    );
}


startButton.addEventListener(
    "click",
    startCall
);


stopButton.addEventListener(
    "click",
    stopCall
);


// ============================================================
// INTERACTIVE BACKGROUND
// ============================================================

const canvas =
    document.getElementById(
        "backgroundCanvas"
    );

const ctx =
    canvas.getContext(
        "2d"
    );


let width =
    window.innerWidth;

let height =
    window.innerHeight;


let mouseX =
    width / 2;

let mouseY =
    height / 2;


const particles = [];


const PARTICLE_COUNT =
    Math.min(
        100,
        Math.floor(
            window.innerWidth / 14
        )
    );


function resizeCanvas() {

    width =
        window.innerWidth;

    height =
        window.innerHeight;


    const ratio =
        Math.min(
            window.devicePixelRatio || 1,
            2
        );


    canvas.width =
        width * ratio;

    canvas.height =
        height * ratio;


    canvas.style.width =
        `${width}px`;

    canvas.style.height =
        `${height}px`;


    ctx.setTransform(
        ratio,
        0,
        0,
        ratio,
        0,
        0
    );
}


window.addEventListener(
    "resize",
    resizeCanvas
);


window.addEventListener(
    "mousemove",
    (event) => {

        mouseX =
            event.clientX;

        mouseY =
            event.clientY;
    }
);


function createParticle() {

    return {

        x:
            Math.random() *
            width,

        y:
            Math.random() *
            height,

        vx:
            (Math.random() - 0.5)
            * 0.35,

        vy:
            (Math.random() - 0.5)
            * 0.35,

        radius:
            Math.random()
            * 1.7
            + 0.5,

        phase:
            Math.random()
            * Math.PI
            * 2,
    };
}


for (
    let i = 0;
    i < PARTICLE_COUNT;
    i++
) {

    particles.push(
        createParticle()
    );
}


function drawBackground() {

    ctx.clearRect(
        0,
        0,
        width,
        height
    );


    const gradient =
        ctx.createRadialGradient(
            mouseX,
            mouseY,
            20,
            width / 2,
            height / 2,
            Math.max(
                width,
                height
            )
        );


    gradient.addColorStop(
        0,
        "rgba(70,100,190,0.12)"
    );

    gradient.addColorStop(
        0.45,
        "rgba(70,50,160,0.06)"
    );

    gradient.addColorStop(
        1,
        "rgba(5,8,22,0)"
    );


    ctx.fillStyle =
        gradient;


    ctx.fillRect(
        0,
        0,
        width,
        height
    );


    const now =
        performance.now()
        / 1000;


    for (
        let i = 0;
        i < particles.length;
        i++
    ) {

        const particle =
            particles[i];


        particle.x +=
            particle.vx;

        particle.y +=
            particle.vy;


        if (
            particle.x < 0 ||
            particle.x > width
        ) {

            particle.vx *=
                -1;
        }


        if (
            particle.y < 0 ||
            particle.y > height
        ) {

            particle.vy *=
                -1;
        }


        const dx =
            mouseX -
            particle.x;

        const dy =
            mouseY -
            particle.y;


        const distance =
            Math.sqrt(
                dx * dx +
                dy * dy
            );


        if (
            distance < 220
        ) {

            particle.x +=
                (dx / Math.max(
                    distance,
                    1
                )) * 0.10;

            particle.y +=
                (dy / Math.max(
                    distance,
                    1
                )) * 0.10;
        }


        const glow =
            0.3 +
            Math.sin(
                now +
                particle.phase
            ) * 0.12;


        ctx.beginPath();

        ctx.arc(
            particle.x,
            particle.y,
            particle.radius,
            0,
            Math.PI * 2
        );


        ctx.fillStyle =
            `rgba(130,160,255,${glow})`;

        ctx.fill();
    }


    requestAnimationFrame(
        drawBackground
    );
}


resizeCanvas();

drawBackground();


// ============================================================
// INITIAL STATE
// ============================================================

setConnection(
    false
);

setVoiceStatus(
    "Ready"
);

setOrbState(
    "idle"
);

updateMessageCount();