import os
from typing import TypedDict, List, Union
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse
from langchain_core.messages import HumanMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END

# Load environment variables (make sure GROQ_API_KEY is set in .env)
load_dotenv()

# Define agent state
class AgentState(TypedDict):
    messages: List[Union[HumanMessage, AIMessage]]

# Initialize Groq LLM
llm = ChatGroq(
    model="llama-3.1-8b-instant",   # Free LLaMA model on Groq
    temperature=0.7
)

# Define process function for LangGraph
def process(state: AgentState) -> AgentState:
    response = llm.invoke(state["messages"])
    state["messages"].append(AIMessage(content=response.content))
    return state

# Build LangGraph agent
graph = StateGraph(AgentState)
graph.add_node("process", process)
graph.add_edge(START, "process")
graph.add_edge("process", END)
agent = graph.compile()

# Store conversation history in memory
conversation_history: List[Union[HumanMessage, AIMessage]] = []

# FastAPI app
app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your extension's origin for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class UserInput(BaseModel):
    message: str

@app.post("/chat")
def chat(user_input: UserInput):
    global conversation_history
    conversation_history.append(HumanMessage(content=user_input.message))
    result = agent.invoke({"messages": conversation_history})
    conversation_history = result["messages"]
    ai_message = conversation_history[-1].content
    return {"response": ai_message}

@app.get("/")
def root():
    return {"message": "Groq Chatbot API is running!"}

@app.get("/widget.js", response_class=PlainTextResponse)
def get_widget_js():
    js_code = f"""
    (function () {{
      const API_URL = "{os.getenv('PUBLIC_API_URL', 'http://localhost:8000/chat')}";

      // Inject styles
      const style = document.createElement("style");
      style.innerHTML = `
        #groq-chat-bubble {{
          position: fixed;
          bottom: 20px;
          right: 20px;
          width: 60px;
          height: 60px;
          border-radius: 50%;
          background: #4CAF50;
          color: white;
          font-size: 28px;
          text-align: center;
          line-height: 60px;
          cursor: pointer;
          box-shadow: 0 4px 10px rgba(0,0,0,0.3);
          z-index: 9999;
        }}
        #groq-chat-container {{
          display: none;
          position: fixed;
          bottom: 90px;
          right: 20px;
          width: 300px;
          height: 400px;
          border-radius: 10px;
          box-shadow: 0 4px 20px rgba(0,0,0,0.3);
          background: white;
          overflow: hidden;
          z-index: 10000;
          font-family: sans-serif;
          display: flex;
          flex-direction: column;
        }}
        #chat-window {{
          flex: 1;
          overflow-y: auto;
          padding: 10px;
          font-size: 14px;
        }}
        .message {{ margin: 5px 0; padding: 8px 12px; border-radius: 12px; max-width: 80%; }}
        .user {{ background: #DCF8C6; align-self: flex-end; }}
        .ai {{ background: #F1F0F0; align-self: flex-start; }}
        .error {{ background: #FFCDD2; color: red; }}
        #chat-form {{ display: flex; border-top: 1px solid #ccc; }}
        #user-input {{ flex: 1; border: none; padding: 10px; font-size: 14px; outline: none; }}
        #chat-form button {{ background: #4CAF50; color: white; border: none; padding: 0 15px; cursor: pointer; }}
      `;
      document.head.appendChild(style);

      // Bubble
      const bubble = document.createElement("div");
      bubble.id = "groq-chat-bubble";
      bubble.textContent = "💬";
      document.body.appendChild(bubble);

      // Container
      const container = document.createElement("div");
      container.id = "groq-chat-container";
      container.innerHTML = `
        <div id="chat-window"></div>
        <form id="chat-form">
          <input type="text" id="user-input" placeholder="Type your message..." required />
          <button type="submit">➤</button>
        </form>
      `;
      document.body.appendChild(container);

      const chatWindow = container.querySelector("#chat-window");
      const chatForm = container.querySelector("#chat-form");
      const userInput = container.querySelector("#user-input");

      function appendMessage(content, sender) {{
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${{sender}}`;
        msgDiv.textContent = content;
        chatWindow.appendChild(msgDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
      }}

      async function sendMessage(message) {{
        appendMessage(message, "user");
        try {{
          const res = await fetch(API_URL, {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ message }}),
          }});
          if (!res.ok) throw new Error("Network error");
          const data = await res.json();
          appendMessage(data.response, "ai");
        }} catch (err) {{
          appendMessage("⚠️ " + err.message, "error");
        }}
      }}

      chatForm.addEventListener("submit", (e) => {{
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;
        userInput.value = "";
        sendMessage(message);
      }});

      bubble.addEventListener("click", () => {{
        container.style.display = container.style.display === "none" ? "flex" : "none";
      }});
    }})();
    """
    return js_code
