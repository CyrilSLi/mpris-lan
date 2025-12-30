function createSilentAudio(time) {
    const dataSize = Math.ceil(time * 8000);
    const byteLength = 44 + dataSize;
    const view = new DataView(new ArrayBuffer(byteLength));

    view.setUint32(0, 0x52494646, false);    // Chunk ID "RIFF"
    view.setUint32(4, 36 + dataSize, true);  // File size
    view.setUint32(8, 0x57415645, false);    // Format "WAVE"
    view.setUint32(12, 0x666D7420, false);   // Sub-chunk 1 ID "fmt "
    view.setUint32(16, 16, true);            // Sub-chunk 1 size
    view.setUint16(20, 1, true);             // Audio format
    view.setUint16(22, 1, true);             // Number of channels
    view.setUint32(24, 8000, true);          // Sample rate
    view.setUint32(28, 8000, true);          // Byte rate
    view.setUint16(32, 1, true);             // Block align
    view.setUint16(34, 8, true);             // Bits per sample
    view.setUint32(36, 0x64617461, false);   // Sub-chunk 2 ID "data"
    view.setUint32(40, dataSize, true);      // Sub-chunk 2 size

    for (let offset = 44; offset < byteLength; offset++) {
        view.setUint8(offset, 128);
    }
    return URL.createObjectURL(new Blob([view], { type: "audio/wav" }));
}

const audioEl = document.createElement("audio");

window.updateMedia = (length, position, playing) => {
    if (length !== audioEl.duration) {
        audioEl.src = createSilentAudio(length);
    }
    audioEl.play().then(() => {
        if (!playing) {
            audioEl.pause();
        }
        navigator.mediaSession.setPositionState({
            duration: audioEl.duration,
            playbackRate: 1,
            position: position
        });
    }).catch(() => {});
}

window.stopMediaSession = () => {
    updateMedia(0.1, 0, false);
}

window.clearMediaSession = () => {
    audioEl.src = "";
}

navigator.mediaSession.setActionHandler("seekbackward", () => {
    window.mediaSessionEvent("seekbackward", null);
});

navigator.mediaSession.setActionHandler("seekforward", () => {
    window.mediaSessionEvent("seekforward", null);
});

navigator.mediaSession.setActionHandler("play", () => {
    window.mediaSessionEvent("play", null);
});

navigator.mediaSession.setActionHandler("pause", () => {
    window.mediaSessionEvent("pause", null);
});

navigator.mediaSession.setActionHandler("seekto", (ev) => {
    window.mediaSessionEvent("seekto", ev.seekTime);
});