document.addEventListener("DOMContentLoaded", () => {
  chrome.storage.sync.get(
    ["language", "debugMode", "server", "apiKey"],
    (data) => {
      document.getElementById("language").value = data.language || "English";
      document.getElementById("server").value =
        data.server || "http://127.0.0.1:9990";
      document.getElementById("debugMode").checked = data.debugMode || false;
      document.getElementById("apiKey").value = data.apiKey || "";
    }
  );
});

document.getElementById("save").addEventListener("click", function () {
  const language = document.getElementById("language").value;
  const server = document.getElementById("server").value;
  const debugMode = document.getElementById("debugMode").checked;
  const apiKey = document.getElementById("apiKey").value;

  chrome.storage.sync.set({ language, server, debugMode, apiKey }, function () {
    console.log("Language, Server, Debug Mode and API Key settings saved");
  });
});
