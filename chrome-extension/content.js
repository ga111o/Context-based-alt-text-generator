const currentUrl = window.location.href;
const targetUrl = `http://127.0.0.1:9990/url?url=${encodeURIComponent(
  currentUrl
)}`;

fetch(targetUrl)
  .then((response) => {
    console.log("success - fetch(targetUrl):", response);
  })
  .catch((error) => {
    console.error("error - fetch(targetUrl):", error);
  });

async function updateImageAltText() {
  const response = await fetch("http://127.0.0.1:9990/output");
  if (!response.ok) {
    console.error("failed to fetch alt texts");
    return;
  }

  const altTexts = await response.json();

  document.querySelectorAll("img").forEach((img) => {
    const imageName = img.src.split("/").pop();
    console.log(`img name: ${imageName}`);
    if (altTexts[imageName]) {
      img.alt = altTexts[imageName].response;
    }
  });
}

// if (document.readyState === "loading") {
//   document.addEventListener("DOMContentLoaded", updateImageAltText());
// } else {
//   updateImageAltText();
// }
// 이거 왜 작동을 안하는 거지

setInterval(function () {
  console.log("working...");
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", updateImageAltText);
  } else {
    updateImageAltText();
  }
}, 10000);
