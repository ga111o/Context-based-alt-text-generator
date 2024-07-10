let debugMode = false;
const currentUrl = window.location.href;
let session = new Date().getTime();
let server = "";

chrome.storage.sync.get(
  ["model", "debugMode", "server", "apiKey", "language"],
  function (data) {
    let model = data.model || "caption";
    debugMode = !!data.debugMode;
    server = data.server || "http://223.194.20.119:9919";
    let apiKey = data.apiKey || "";
    let language = data.language || "English";

    const targetUrl = `${server}/url?url=${encodeURIComponent(
      currentUrl
    )}&model=${model}&session=${session}&title=${encodeURIComponent(
      document.title
    )}&language=${encodeURIComponent(language)}`;

    if (apiKey) {
      fetch(`${server}/apikey`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ apiKey: apiKey, session: session }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (debugMode) console.log("success - fetch api key: ", data);
        })
        .catch((error) => {
          if (debugMode) console.error("error - fetch api key:", error);
        });

      fetch(targetUrl)
        .then((response) => {
          if (debugMode) console.log("success - fetch(targetUrl):", response);
        })
        .catch((error) => {
          if (debugMode) console.error("error - fetch(targetUrl):", error);
        });
    }
  }
);

async function updateImageAltText() {
  const response = await fetch(`${server}/${session}/output`);
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
