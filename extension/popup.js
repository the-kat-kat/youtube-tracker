fetch("https://youtube-tracker-production-2dbe.up.railway.app/daily")
        .then(r => r.json())
        .then(days => {
            const seconds = days[0]?.total_seconds || 0;
            const m = Math.floor(seconds / 60);
            const s = seconds % 60;
            document.getElementById("today-time").textContent = `Today: ${m}m ${s}s watched`;
});