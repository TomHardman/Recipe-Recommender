import React, { useState } from "react";
import "./App.css";
import ChatBox from "./Chatbox";
import Sidebar from "./Sidebar";

function App() {
    const [chats, setChats] = useState([
        { chat_id: 1, chat_title: "Chat 1", thread_id: 1},
        { chat_id: 2, chat_title: "Chat 2", thread_id: 2},
        { chat_id: 3, chat_title: "Chat 3", thread_id: 3},
    ]);

    const handleChatSelect = (chat_id) => {
        console.log("Selected Chat ID:", chat_id);
        // You can add more functionality here, e.g., loading chat messages in ChatBox
    };

    const handleAddChat = () => {
        setChats((prevChats) => [
            ...prevChats,
            { chat_id: prevChats.length + 1, chat_title: `Chat ${prevChats.length + 1}`, thread_id: prevChats.length + 1},
        ]);
    };

    return (
        <div className="App">
            <Sidebar chats={chats} onChatSelect={handleChatSelect} onAddChat={handleAddChat} />
            <ChatBox />
        </div>
    );
}

export default App;
