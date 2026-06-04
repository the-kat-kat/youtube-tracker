chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log("Background recieved messageee", message);
    if (message.type == "TRACK_VIDEO") {
        fetch("http://127.0.0.1:5000/track", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({video_id: message.videoId})
        }).then(() => {
            sendResponse({status: "ok"});
        })
        .catch(err => {
            sendResponse({error: err.message });
    });
    }

    return true;
}) 