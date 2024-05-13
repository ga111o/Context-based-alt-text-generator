let debugMode = false;
const currentUrl = window.location.href;

chrome.storage.sync.get(["language", "debugMode"], function (data) {
  let language = data.language || "English";
  debugMode = !!data.debugMode;

  const targetUrl = `http://127.0.0.1:9990/url?url=${encodeURIComponent(
    currentUrl
  )}&language=${encodeURIComponent(language)}`;

  fetch(targetUrl)
    .then((response) => {
      if (debugMode) console.log("success - fetch(targetUrl):", response);
    })
    .catch((error) => {
      if (debugMode) console.error("error - fetch(targetUrl):", error);
    });
});

async function updateImageAltText() {
  const response = await fetch("http://127.0.0.1:9990/output");
  if (!response.ok) {
    if (debugMode) console.error("failed to fetch alt texts");
    return;
  }

  const altTexts = await response.json();

  document.querySelectorAll("img").forEach((img) => {
    const imageName = img.src.split("/").pop();
    if (altTexts[imageName]) {
      img.alt = altTexts[imageName].response;
      if (debugMode) console.log(`Alt text updated for image: ${imageName}`);
    }
  });
}

setInterval(function () {
  if (debugMode) console.log("working...");
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", updateImageAltText);
  } else {
    updateImageAltText();
  }
}, 5000);

fetchWithUserLanguage();
