import React, { useState, useRef, useEffect } from "react";
import axios from "axios";

const ChatBox = () => {
    const [messages, setMessages] = useState([]); // Store chat messages
    const [input, setInput] = useState(""); // Store user input
    const [loading, setLoading] = useState(false); // Store loading state
    const messagesEndRef = useRef(null); // Create a ref for the end of the messages
    const eventSourceRef = useRef(null); // Ref to track the EventSource instance
    const firstTokenReceivedRef = useRef(false); // Use ref to track first token reception


    // Function to send message to the backend and start streaming the response
    const sendMessage = async () => {
        if (!input.trim() || loading) return; // Skip if input is empty

        // Add user message to chat
        const userMessage = { role: "user", content: input };
        setMessages((prevMessages) => [...prevMessages, userMessage]);
        firstTokenReceivedRef.current = false;
        setLoading(true);
        setInput(""); // Clear input field

        // Close any existing event source
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
        }

        // Initialize EventSource for streaming
        eventSourceRef.current = new EventSource(`http://127.0.0.1:8000/stream?message=${encodeURIComponent(input)}`);

        eventSourceRef.current.onmessage = (event) => {
            if (!firstTokenReceivedRef.current) {
                firstTokenReceivedRef.current = true; // Set ref to true immediately
                setMessages((prevMessages) => [
                    ...prevMessages,
                    { role: "agent", content: event.data }
                ]);
                setLoading(false);
            } 
            else {
                setMessages((prevMessages) => {
                    console.log("Message concat:", event.data, event.data.includes('\n'))
                    // Use functional update to ensure the latest state is used
                    return prevMessages.map((msg, index) => {
                        if (index === prevMessages.length - 1 && msg.role === "agent") {
                            // Return a new object with updated content
                            return { ...msg, content: msg.content + event.data.replace(/<br>/g, '\n')};
                        }
                        return msg; // Return other messsages unchanged
                    });
                });
            }
        };

        // Handle any errors in the streaming connection
        eventSourceRef.current.onerror = (error) => {
            console.error("SSE error:", error);
            eventSourceRef.current.close();
            setLoading(false);
        };

        // Close the connection and stop loading once streaming is finished
        eventSourceRef.current.addEventListener("end-of-stream", () => {
            setLoading(false);
            eventSourceRef.current.close();
        });
    };

    // Update input state on user input
    const handleInputChange = (e) => setInput(e.target.value);

    // Handle Enter key press for sending message
    const handleKeyDown = (e) => {
        if (e.key === "Enter") sendMessage();
    };

    // Scroll to the bottom of the messages when a new message is added
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages]);

    // Clean up EventSource when component unmounts
    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
        };
    }, []);

    return (
        <div style={{ padding: "20px", maxWidth: "600px", margin: "auto" }}>
            <h2>Recipe Chat Assistant</h2>
            <div style={{ height: "500px", overflowY: "scroll", border: "1px solid #ccc", padding: "10px", marginBottom: "10px" }}>
                {messages.map((msg, index) => (
                    <div key={index} style={{ textAlign: msg.role === "user" ? "right" : "left" }}>
                        <p style={{ 
                            backgroundColor: msg.role === "user" ? "#e6f7ff" : "#f0f0f0", 
                            display: "inline-block", 
                            padding: "10px 20px", 
                            borderRadius: "20px", 
                            maxWidth: "80%", 
                            whiteSpace: "pre-wrap"
                        }}>
                            {msg.content}
                        </p>
                    </div>
                ))}
                {/* Display a "Thinking..." message while loading */}
                {loading && (
                    <div style={{ textAlign: "left" }}>
                        <p style={{ 
                            backgroundColor: "#f0f0f0", 
                            display: "inline-block", 
                            padding: "10px 20px", 
                            borderRadius: "20px", 
                            maxWidth: "80%", 
                            whiteSpace: "pre-wrap" 
                        }}>
                            Thinking...
                        </p>
                    </div>
                )}
                <div ref={messagesEndRef} /> {/* This div serves as a scroll anchor */}
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