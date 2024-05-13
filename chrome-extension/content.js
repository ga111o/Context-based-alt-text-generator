// content.js

const currentUrl = window.location.href;

function fetchWithUserLanguage() {
  chrome.storage.sync.get("language", function (data) {
    let language = data.language;
    if (!language) {
      language = "English";
    }

    const targetUrl = `http://127.0.0.1:9990/url?url=${encodeURIComponent(
      currentUrl
    )}&language=${encodeURIComponent(language)}`;

    fetch(targetUrl)
      .then((response) => {
        // console.log("success - fetch(targetUrl):", response);
      })
      .catch((error) => {
        // console.error("error - fetch(targetUrl):", error);
      });
  });
}

async function updateImageAltText() {
  const response = await fetch("http://127.0.0.1:9990/output");
  if (!response.ok) {
    // console.error("failed to fetch alt texts");
    return;
  }

  const altTexts = await response.json();

  document.querySelectorAll("img").forEach((img) => {
    const imageName = img.src.split("/").pop();
    // console.log(`img name: ${imageName}`);
    if (altTexts[imageName]) {
      img.alt = altTexts[imageName].response;
    }
  });
}

setInterval(function () {
  console.log("working...");
  console.log(`targetUrl: ${targetUrl}`);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", updateImageAltText);
  } else {
    updateImageAltText();
  }
}, 10000);

fetchWithUserLanguage();
