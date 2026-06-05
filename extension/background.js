const GOOGLE_SCRIPT_URL="https://script.google.com/macros/s/AKfycbwfoy2u78o0tOelVeH7o-H4IChLaqmh9hafNpTpKnZHmDNg-Ygl19Dunnic-GarrWmQjA/exec";


chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log("Background recieved messageee", message);
    if (message.type == "TRACK_VIDEO") {
        fetch("http://127.0.0.1:5001/track", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({video_id: message.videoId, secondsWatched: message.secondsWatched})
        })
        .then(res => res.json())
        .then((data)=> {
            console.log("response from backend", data);

            if (data && data.shouldSendEmail) {
                console.log("should send email!");
                fetch(GOOGLE_SCRIPT_URL, {method: "POST"})
                .then(() => console.log("sent email"))
                .catch(err => console.error("error sending email", err));
            }
            sendResponse({status: "ok"});
        })
        .catch(err => {
            sendResponse({error: err.message });
        });
    }

    return true;
});
