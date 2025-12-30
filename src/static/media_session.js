function createSilentAudio(time) {
    const bufferLength = time * 44100;
    const AudioContext = window.AudioContext || window.webkitAudioContext || window.mozAudioContext;
    if (!AudioContext) {
        console.log("No Audio Context")
    }
    const context = new AudioContext();
    const audioFile = context.createBuffer(1, bufferLength, 44100);

    let numOfChan = audioFile.numberOfChannels,
        length = bufferLength * numOfChan * 2 + 44,
        buffer = new ArrayBuffer(length),
        view = new DataView(buffer),
        channels = [], i, sample,
        offset = 0,
        pos = 0;

    function setUint16(data) {
        view.setUint16(pos, data, true);
        pos += 2;
    }

    function setUint32(data) {
        view.setUint32(pos, data, true);
        pos += 4;
    }

    setUint32(0x46464952);
    setUint32(length - 8);
    setUint32(0x45564157);

    setUint32(0x20746d66);
    setUint32(16);
    setUint16(1);
    setUint16(numOfChan);
    setUint32(audioFile.sampleRate);
    setUint32(audioFile.sampleRate * 2 * numOfChan);
    setUint16(numOfChan * 2);
    setUint16(16);

    setUint32(0x61746164);
    setUint32(length - pos - 4);

    for (i = 0; i < audioFile.numberOfChannels; i++)
        channels.push(audioFile.getChannelData(i));

    while (pos < length) {
        for (i = 0; i < numOfChan; i++) {
            sample = Math.max(-1, Math.min(1, channels[i][offset]));
            sample = (0.5 + sample < 0 ? sample * 32768 : sample * 32767) | 0;
            view.setInt16(pos, sample, true);
            pos += 2;
        }
        offset++;
    }
    return URL.createObjectURL(new Blob([buffer], { type: "audio/wav" }));
}

const audioEl = document.createElement("audio");
window.audioEl = audioEl;
// window.mediaSessionAction = null;
audioEl.src = createSilentAudio(0.01);

window.updateMedia = (length, position) => {
    if (length !== audioEl.duration) {
        audioEl.src = createSilentAudio(length);
    }
    audioEl.play().then(() => navigator.mediaSession.setPositionState({
        duration: audioEl.duration,
        playbackRate: audioEl.playbackRate,
        position: position
    })).catch(() => {});
}

window.stopMediaSession = () => {
    updateMedia(0.01, 0);
}

window.clearMediaSession = () => {
    audioEl.src = "";
}

/* window.updateMedia = function(length, position, isPlaying) {
    if (length !== audioEl.duration) {
        audioEl.src = createSilentAudio(length);
    }
    audioEl.load();
    audioEl.play().then(() => window.updateMetadata()).catch(() => {});
    console.log("isPlaying", isPlaying);
    if (!isPlaying) {
        audioEl.pause();
    }
    audioEl.currentTime = position;
}

window.updateMetadata = function(title, artist, album, artwork) {
    navigator.mediaSession.metadata = new MediaMetadata({
        title: title || "Title N/A",
        artist: artist || "Artist N/A",
        album: album || "Album N/A",
        artwork: artwork || []
    });
    updatePositionState();
}

function updatePositionState() {
    if ("setPositionState" in navigator.mediaSession) {
        navigator.mediaSession.setPositionState({
            duration: audioEl.duration,
            playbackRate: audioEl.playbackRate,
            position: audioEl.currentTime
        });
    }
}

navigator.mediaSession.setActionHandler("previoustrack", () => {
    window.dispatchEvent(new CustomEvent("mediaSessionEvent", { detail: { type: "previousTrack" } }));
});

navigator.mediaSession.setActionHandler("nexttrack", () => {
    window.dispatchEvent(new CustomEvent("mediaSessionEvent", { detail: { type: "nextTrack" } }));
});

navigator.mediaSession.setActionHandler("seekforward", (ev) => {
    window.mediaSessionAction = "seekForward";
    console.log("seek forward");
    audioEl.currentTime += 10;
    updatePositionState();
});

navigator.mediaSession.setActionHandler("seekbackward", (ev) => {
    window.mediaSessionAction = "seekBackward";
    console.log("seek backward");
    audioEl.currentTime -= 10;
    updatePositionState();
});

navigator.mediaSession.setActionHandler("play", async () => {
    window.dispatchEvent(new CustomEvent("mediaSessionEvent", { detail: { type: "play-pause" }}));
    await audioEl.play();
});

navigator.mediaSession.setActionHandler("pause", () => {
    window.dispatchEvent(new CustomEvent("mediaSessionEvent", { detail: { type: "play-pause" }}));
    audioEl.pause();
});

audioEl.addEventListener("play", () => {
    navigator.mediaSession.playbackState = "playing";
});

audioEl.addEventListener("pause", () => {
    navigator.mediaSession.playbackState = "paused";
});

navigator.mediaSession.setActionHandler("seekto", (ev) => {
    window.dispatchEvent(new CustomEvent("mediaSessionEvent", { detail: {
        type: "seekTo", seekTime: ev.seekTime 
    }}));
}); */