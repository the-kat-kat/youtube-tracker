const GOOGLE_SCRIPT_URL="https://script.google.com/macros/s/AKfycbwfoy2u78o0tOelVeH7o-H4IChLaqmh9hafNpTpKnZHmDNg-Ygl19Dunnic-GarrWmQjA/exec";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log("Background recieved messageee", message);
    if (message.type == "TRACK_VIDEO") {
        fetch("http://127.0.0.1:5001/track", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({video_id: message.videoId, secondsWatched: message.secondsWatched})
        }).then(() => {
            sendResponse({status: "ok"});
        })
        .catch(err => {
            sendResponse({error: err.message });
        });
    }

    return true;
});
