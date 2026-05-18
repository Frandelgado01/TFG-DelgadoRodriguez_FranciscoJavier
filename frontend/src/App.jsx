import { useState } from 'react';
import axios from 'axios';
import { Send, Bot, User, Wine } from 'lucide-react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '¡Hola! Soy tu Asistente Normativo Vitivinícola. Puedes preguntarme sobre el Cuaderno Digital, normativas de viñedos o tratamientos fitosanitarios.'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    // Añadimos el mensaje del usuario al chat
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setInput('');
    setIsLoading(true);

    try {
      // Llamada a tu Backend local de FastAPI
      const response = await axios.post('http://127.0.0.1:8000/ask', {
        question: userMessage
      });

      // Añadimos la respuesta del RAG al chat
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources
      }]);
    } catch (error) {
      console.error("Error de conexión:", error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Lo siento, no he podido conectar con el cerebro del sistema. Asegúrate de que el backend está corriendo en el puerto 8000.'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      {/* Cabecera */}
      <header className="chat-header">
        <Wine className="header-icon" size={28} />
        <h1>Asistente Normativo Vitivinícola</h1>
      </header>

      {/* Historial de Mensajes */}
      <main className="chat-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message-wrapper ${msg.role}`}>
            <div className="avatar">
              {msg.role === 'assistant' ? <Bot size={20} /> : <User size={20} />}
            </div>
            <div className="message-content">
              <p>{msg.content}</p>

              {/* Renderizado de las Fuentes (Citas) */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="sources-container">
                  <span className="sources-title">Fuentes consultadas:</span>
                  <div className="sources-list">
                    {msg.sources.map((source, i) => (
                      <span key={i} className="source-tag">{source}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message-wrapper assistant">
            <div className="avatar"><Bot size={20} /></div>
            <div className="message-content loading">
              <span className="dot"></span><span className="dot"></span><span className="dot"></span>
            </div>
          </div>
        )}
      </main>

      {/* Input de texto */}
      <footer className="chat-input-area">
        <form onSubmit={handleSend}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Escribe tu consulta sobre la normativa..."
            disabled={isLoading}
          />
          <button type="submit" disabled={!input.trim() || isLoading}>
            <Send size={20} />
          </button>
        </form>
      </footer>
    </div>
  );
}

export default App;