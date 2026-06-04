let lastVideoId = null;

function getVideoId() {
    const url = new URL(window.location.href);
    return url.searchParams.get("v");
}

function sendVideo(videoId) {
    chrome.runtime.sendMessage({type: "TRACK_VIDEO", videoId: videoId});
}

function checkForVideo() {
    const videoId = getVideoId();
    if (videoId && videoId !== lastVideoId) {
        lastVideoId = videoId;
        sendVideo(videoId);
    }
}

setInterval(checkForVideo, 2000); 