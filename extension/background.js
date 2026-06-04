chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type == "TRACK_VIDEO") {
        fetch("http://localhost:5000/track", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({video_id: message.videoId})
        }).then(() => sendReponse({status: "ok"}))
        .catch(err => sendResponse({error: err.message}));
        return true;
    }
}) 