let lastVideoId = null;
let videoStartTime = null;

function getVideoId() {
    const url = new URL(window.location.href);
    return url.searchParams.get("v");
}

function sendVideo(videoId, secondsWatched) {
    console.log("sending video", videoId, "seconds", secondsWatched);
    chrome.runtime.sendMessage({
        type: "TRACK_VIDEO",
        videoId: videoId,
        secondsWatched: secondsWatched
    });
}

function checkForVideo() {
    const videoId = getVideoId();
    if (videoId && videoId !== lastVideoId) {
        if (lastVideoId && videoStartTime) {
            const secondsWatched = Math.round((Date.now() - videoStartTime) / 1000);
            sendVideo(lastVideoId, secondsWatched);
        }
        lastVideoId = videoId;
        videoStartTime = Date.now();
        sendVideo(videoId, 0);
    }
}

document.addEventListener("visibilitychange", () => {
    if (document.hidden && lastVideoId && videoStartTime) {
        const secondsWatched = Math.round((Date.now() - videoStartTime) / 1000);
        console.log("tab hidden, seconds watched:", secondsWatched);
        sendVideo(lastVideoId, secondsWatched);
        videoStartTime = Date.now();
    } else if (!document.hidden) {
        console.log("tab visible again");
        videoStartTime = Date.now();
    }
});

setInterval(checkForVideo, 2000);