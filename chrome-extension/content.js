async function updateImageAltText() {
  const response = await fetch("http://127.0.0.1:8123/output");
  if (!response.ok) {
    console.error("Failed to fetch alt texts");
    return;
  }

  const altTexts = await response.json();

  document.querySelectorAll("img").forEach((img) => {
    const imageName = img.src.split("/").pop();
    if (altTexts[imageName]) {
      img.alt = altTexts[imageName].response;
    } else if (!img.alt) {
      img.alt = "no exist alt";
    }
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", updateImageAltText);
} else {
  updateImageAltText();
}
