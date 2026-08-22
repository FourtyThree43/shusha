// Popup script for Shusha WebExtension

const SERVER_BASE = "http://127.0.0.1:6810";

document.addEventListener("DOMContentLoaded", async () => {
  const badge = document.getElementById("badge");
  const addBtn = document.getElementById("addBtn");
  const urlInput = document.getElementById("urlInput");
  const statusDiv = document.getElementById("status");

  // Check health
  try {
    const resp = await fetch(`${SERVER_BASE}/health`, { method: "GET" });
    if (resp.ok) {
      badge.textContent = "● Daemon Online";
      badge.className = "badge online";
    } else {
      badge.textContent = "● Offline";
      badge.className = "badge offline";
    }
  } catch (e) {
    badge.textContent = "● Offline";
    badge.className = "badge offline";
  }

  addBtn.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    if (!url) {
      statusDiv.textContent = "Please enter a valid URL";
      statusDiv.style.color = "#ef4444";
      return;
    }

    try {
      statusDiv.textContent = "Sending to Shusha...";
      statusDiv.style.color = "#94a3b8";

      const res = await fetch(`${SERVER_BASE}/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url })
      });

      if (res.ok) {
        statusDiv.textContent = "✓ Queued in Shusha!";
        statusDiv.style.color = "#00bc8c";
        urlInput.value = "";
        setTimeout(() => window.close(), 1200);
      } else {
        statusDiv.textContent = "Error sending URL";
        statusDiv.style.color = "#ef4444";
      }
    } catch (err) {
      statusDiv.textContent = "Failed to connect to Shusha (is app running?)";
      statusDiv.style.color = "#ef4444";
    }
  });
});
