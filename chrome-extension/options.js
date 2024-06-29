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

document.getElementById("save").addEventListener("click", async function () {
  const language = document.getElementById("language").value;
  const server = document.getElementById("server").value;
  const debugMode = document.getElementById("debugMode").checked;
  const apiKey = document.getElementById("apiKey").value;
  const apiKeyErrorElement = document.getElementById("apiKeyError");

  const isValidApiKey = await validateApiKey(apiKey);
  if (!isValidApiKey) {
    apiKeyErrorElement.style.display = "block";
    return;
  } else {
    apiKeyErrorElement.style.display = "none";
  }

  chrome.storage.sync.set({ language, server, debugMode, apiKey }, function () {
    console.log("saved language, Server, Debug Mode and API Key settings");
  });
});

async function validateApiKey(apiKey) {
  try {
    const response = await fetch("https://api.openai.com/v1/engines", {
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
    });
    return response.ok;
  } catch (error) {
    console.error("api Key err:", error);
    return false;
  }
}
