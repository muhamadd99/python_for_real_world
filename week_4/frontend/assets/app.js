const form = document.getElementById("receipt-form");
const fileInput = document.getElementById("receipt-file");
const senderInput = document.getElementById("sender");
const resultBox = document.getElementById("result");
const resultJson = document.getElementById("result-json");

const API_BASE = window.API_BASE || "";

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!fileInput.files.length) {
    alert("Please choose a receipt file.");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  formData.append("sender", senderInput.value || "web");

  resultBox.classList.remove("hidden");
  resultJson.textContent = "Uploading...";

  try {
    const response = await fetch(`${API_BASE}/api/receipts`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || "Upload failed");
    }

    const data = await response.json();
    resultJson.textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    resultJson.textContent = `Error: ${error.message}`;
  }
});
