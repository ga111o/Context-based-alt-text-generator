function checkApiKey(apiKey) {
  const apiKeyStatus = document.getElementById("apiKeyStatus");

  if (!apiKey) {
    apiKeyStatus.textContent = "openai api-key is required";
    return;
  }

  fetch("https://api.openai.com/v1/models", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${apiKey}`,
    },
  })
    .then((response) => {
      if (response.ok) {
        apiKeyStatus.textContent = "✅";
      } else {
        apiKeyStatus.textContent = "❌ openai api-key is not correct";
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      apiKeyStatus.textContent = "❌";
    });
}

document.addEventListener("DOMContentLoaded", () => {
  chrome.storage.sync.get(
    ["language", "debugMode", "server", "apiKey"],
    (data) => {
      document.getElementById("language").value = data.language || "English";
      document.getElementById("server").value =
        data.server || "http://127.0.0.1:9990";
      document.getElementById("debugMode").checked = data.debugMode || false;
      document.getElementById("apiKey").value = data.apiKey || "";

      checkApiKey(data.apiKey);
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

    const saveMessage = document.getElementById("saveMessage");
    saveMessage.style.display = "block";

    setTimeout(() => {
      saveMessage.style.display = "none";
    }, 2000);

    checkApiKey(apiKey);
  });
});
