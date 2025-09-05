const API_URL = "http://127.0.0.1:8000/chat"; // Change to deployed backend if needed

const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");

function appendMessage(content, sender) {
  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${sender}`;
  msgDiv.textContent = content;
  chatWindow.appendChild(msgDiv);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendMessage(message) {
  appendMessage(message, "user");

  // Show a temporary loading indicator
  const loadingId = "loading-" + Date.now();
  appendMessage("Thinking...", "loading");
  const loadingElem = chatWindow.lastChild;
  loadingElem.id = loadingId;

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    if (!res.ok) {
      throw new Error(`Server responded with ${res.status}`);
    }

    const data = await res.json();

    // Replace "Thinking..." with AI response
    loadingElem.remove();
    appendMessage(data.response, "ai");
  } catch (err) {
    loadingElem.remove();
    appendMessage("⚠️ Error: " + err.message, "error");
  }
}

// Handle form submit
chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const message = userInput.value.trim();
  if (!message) return;
  userInput.value = "";
  sendMessage(message);
});

// Optional: allow pressing Enter to send without clicking the button
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.requestSubmit();
  }
});