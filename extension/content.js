let lastVideoId = null;

function getVidId() {
    const url = new URL()
    return url.searchParams.get("v");
}

function sendVideo(videoId) {
    fetch("http://localhost:5000/track", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({video_id: videoId})
    });
}

function checkForVideo() {
    const videoId = getVideoId();
    if (videoId && videoId !== lastVideoId) {
        lastVideoId = videoId;
        sendVideo(videoId);
    }
}

setInterval(checkForVideo, 2000); 