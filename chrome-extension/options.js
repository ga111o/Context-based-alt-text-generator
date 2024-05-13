// 저장된 언어 설정을 불러오고 select 요소에 설정합니다.
document.addEventListener("DOMContentLoaded", () => {
  chrome.storage.sync.get("language", (data) => {
    document.getElementById("language").value = data.language || "English";
  });
});

// 사용자가 'Save' 버튼을 클릭하면 선택한 언어를 저장합니다.
document.getElementById("save").addEventListener("click", () => {
  const language = document.getElementById("language").value;
  chrome.storage.sync.set({ language }, () => {
    console.log("Language is set to " + language);
  });
});
