document.addEventListener("DOMContentLoaded", () => {
  chrome.storage.sync.get("language", (data) => {
    document.getElementById("language").value = data.language || "English";
  });
});

document.getElementById("save").addEventListener("click", () => {
  const language = document.getElementById("language").value;
  chrome.storage.sync.set({ language }, () => {
    console.log("Language is set to " + language);
  });
});

document.getElementById("save").addEventListener("click", function () {
  const language = document.getElementById("language").value;
  const debugMode = document.getElementById("debugMode").checked;
  chrome.storage.sync.set({ language, debugMode }, function () {
    console.log("Language and Debug Mode settings saved");
  });
});
