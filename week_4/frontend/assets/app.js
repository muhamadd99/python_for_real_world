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

async function loadReceipts() {
  const tbody = document.getElementById("receipts-tbody");
  try {
    const response = await fetch(`${API_BASE}/api/receipts`);
    if (!response.ok) throw new Error("Failed to load");
    const receipts = await response.json();
    if (!receipts.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="muted">No receipts yet.</td></tr>';
      return;
    }
    tbody.innerHTML = receipts.map(r => `
      <tr>
        <td class="receipt-id">#${r.id}</td>
        <td><span class="receipt-status status-${(r.status || "").toLowerCase()}">${r.status || "UNKNOWN"}</span></td>
        <td>${r.contact_name || r.sender || "—"}</td>
        <td>${r.amount ? "RM" + r.amount : "—"}</td>
        <td>${r.bank_name || "—"}</td>
        <td>${r.receiver_name || "—"}</td>
        <td>${r.transaction_date || "—"}</td>
        <td class="ref-cell">${r.reference_id || "—"}</td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="8" class="muted">Error loading receipts.</td></tr>';
  }
}

loadReceipts();
// Refresh list after upload
form.addEventListener("submit", () => setTimeout(loadReceipts, 3000));
