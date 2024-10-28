// src/ChatBox.js
import React, { useState } from "react";
import axios from "axios";

const ChatBox = () => {
    const [messages, setMessages] = useState([]); // Store chat messages
    const [input, setInput] = useState(""); // Store user input

    // Function to send message to the backend
    const sendMessage = async () => {
        if (!input.trim()) return; // Skip if input is empty
        
        // Add user message to chat
        const userMessage = { role: "user", content: input };
        setMessages([...messages, userMessage]);

        try {
            // Send message to FastAPI backend
            const response = await axios.post("http://127.0.0.1:8000/send_message", {content: input });
            
            // Add agent's response to chat
            const agentMessage = { role: "agent", content: response.data.content };
            setMessages((prevMessages) => [...prevMessages, agentMessage]);
        } catch (error) {
            console.error("Error sending message:", error);
            // Add error message to chat
            const errorMessage = { role: "agent", content: "Error retrieving response." };
            setMessages((prevMessages) => [...prevMessages, errorMessage]);
        }

        setInput(""); // Clear input field
    };

    // Update input state on user input
    const handleInputChange = (e) => setInput(e.target.value);

    // Handle Enter key press for sending message
    const handleKeyDown = (e) => {
        if (e.key === "Enter") sendMessage();
    };

    return (
        <div style={{ padding: "20px", maxWidth: "600px", margin: "auto" }}>
            <h2>Recipe Chat Assistant</h2>
            <div style={{ height: "400px", overflowY: "scroll", border: "1px solid #ccc", padding: "10px", marginBottom: "10px" }}>
                {messages.map((msg, index) => (
                    <div key={index} style={{ textAlign: msg.role === "user" ? "right" : "left" }}>
                        <p style={{ backgroundColor: msg.role === "user" ? "#e6f7ff" : "#f0f0f0", display: "inline-block", padding: "5px 10px", borderRadius: "10px", maxWidth: "80%" }}>
                            {msg.content}
                        </p>
                    </div>
                ))}
            </div>
            <input
                type="text"
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="Type your message..."
                style={{ width: "80%", padding: "10px", marginRight: "5px" }}
            />
            <button onClick={sendMessage} style={{ padding: "10px" }}>
                Send
            </button>
        </div>
    );
};

export default ChatBox;