const GOOGLE_SCRIPT_URL="https://script.google.com/macros/s/AKfycbwfoy2u78o0tOelVeH7o-H4IChLaqmh9hafNpTpKnZHmDNg-Ygl19Dunnic-GarrWmQjA/exec";

let emailSentToday = false;
let emailLastSentDate = null;

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log("Background recieved messageee", message);
    if (message.type == "TRACK_VIDEO") {
        fetch("https://youtube-tracker-cqyn.onrender.com/track", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({video_id: message.videoId, secondsWatched: message.secondsWatched})
        })
        .then(res => {
            console.log("got response status", res.status);
            return res.json();
        })
        .then((data)=> {
            console.log("response from backend", data);
            const today = new Date().toDateString();
            if(emailLastSentDate !== today) {
                emailSentToday = false;
                emailLastSentDate = today;
            }

            if (data && data.shouldSendEmail && !emailSentToday) {
                emailSentToday = true;

                chrome.notifications.create({
                    type: "basic",
                    title: "GET OFF YOUTUBE",
                    iconUrl: "kitty.png",
                    message: "stop wasting time son"
                })

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
