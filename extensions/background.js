// Background Service Worker for Shusha WebExtension

const SHUSHA_WEBHOOK_URL = "http://127.0.0.1:6810/add";

chrome.runtime.onInstalled.addListener(() => {
  // Create context menus
  chrome.contextMenus.create({
    id: "shusha-download-link",
    title: "Download with Shusha",
    contexts: ["link", "video", "audio", "image"]
  });

  chrome.contextMenus.create({
    id: "shusha-download-page",
    title: "Download current page with Shusha",
    contexts: ["page"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  let targetUrl = info.linkUrl || info.srcUrl;
  if (info.menuItemId === "shusha-download-page") {
    targetUrl = info.pageUrl;
  }

  if (targetUrl) {
    sendDownloadToShusha(targetUrl, tab ? tab.url : "");
  }
});

async function sendDownloadToShusha(url, referer = "") {
  try {
    const payload = {
      url: url,
      referer: referer,
      headers: {
        "User-Agent": navigator.userAgent,
        "Referer": referer
      }
    };

    const resp = await fetch(SHUSHA_WEBHOOK_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (resp.ok) {
      console.log("Successfully queued download in Shusha:", url);
    } else {
      console.error("Shusha webhook returned error status:", resp.status);
    }
  } catch (err) {
    console.error("Failed to connect to Shusha daemon on localhost:6810:", err);
  }
}
