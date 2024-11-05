import React, { useState } from "react";

const Sidebar = ({ chats, onChatSelect, onAddChat }) =>{
    const [selectedChatId, setSelectedChatId] = useState(null);

    const handleChatClick = (chatId) => {
        setSelectedChatId(chatId);
        onChatSelect(chatId); // Pass selected chat ID to parent component
    };

    return (
        <div className="sidebar">
            <panel className='panel'>
                <h2>Chats</h2>
                <ul className="chat-list">
                    {chats.map((chat) => (
                        <li
                            key={chat.chat_id}
                            onClick={() => handleChatClick(chat.chat_id)}
                            className={`chat-item ${chat.chat_id === selectedChatId ? "selected" : ""}`}
                        >
                            {chat.chat_title}
                        </li>
                    ))}
                </ul>
                <button className="add-chat-btn" onClick={onAddChat}>
                    +
                </button>
            </panel>
        </div>
    );
}

export default Sidebar;