import React, { useState, useEffect, useRef } from 'react';
import apiClient, { getErrorMessage } from '../api/client';
import { useLanguage } from '../context/LanguageContext';
import ChatBubble from '../components/ChatBubble';
import ErrorMessage from '../components/ErrorMessage';
import { Send, Sparkles, Trash2, ShieldAlert } from 'lucide-react';

const Chat = () => {
  const { t, language } = useLanguage();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Initialize welcome message when language changes or first load
  useEffect(() => {
    setMessages([
      {
        role: 'assistant',
        content: t('chat.welcome_msg'),
        id: 'welcome-init',
      },
    ]);
  }, [language]);

  // Auto-scroll on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSendMessage = async (textToSend) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || loading) return;

    setError('');
    const userMsg = {
      role: 'user',
      content: text,
      id: Date.now().toString(),
    };

    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInputMessage('');
    setLoading(true);

    try {
      // Send message history formatted for backend
      const payloadMessages = newMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await apiClient.post('/api/chat', {
        messages: payloadMessages,
        language,
      });

      const assistantMsg = {
        role: 'assistant',
        content: response.data.reply,
        id: (Date.now() + 1).toString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to get answer. Please try again.'));
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        role: 'assistant',
        content: t('chat.welcome_msg'),
        id: 'welcome-reset',
      },
    ]);
    setError('');
  };

  const quickPills = [
    t('chat.quick_pill1'),
    t('chat.quick_pill2'),
    t('chat.quick_pill3'),
  ];

  return (
    <div className="max-w-4xl mx-auto flex flex-col h-[calc(100vh-12rem)] min-h-[550px]">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-3 border-b border-emerald-100 flex-shrink-0">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-stone-900 tracking-tight flex items-center gap-2">
            <span>{t('chat.title')}</span>
          </h1>
          <p className="text-xs sm:text-sm text-stone-600 font-medium">
            {t('chat.subtitle')}
          </p>
        </div>

        <button
          onClick={handleClearChat}
          type="button"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-stone-100 hover:bg-red-50 text-stone-600 hover:text-red-700 text-xs sm:text-sm font-bold transition-colors"
          title="Clear Conversation"
        >
          <Trash2 className="w-4 h-4" />
          <span className="hidden sm:inline">Clear</span>
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto py-4 px-1 sm:px-2 space-y-2">
        {messages.map((m) => (
          <ChatBubble key={m.id} message={m} />
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex gap-3 items-center my-3 text-stone-500">
            <div className="w-10 h-10 rounded-2xl bg-emerald-700 text-white flex items-center justify-center flex-shrink-0 shadow-sm text-lg select-none">
              🌾
            </div>
            <div className="bg-white border-2 border-emerald-100 rounded-3xl px-5 py-3 shadow-sm flex items-center gap-2">
              <span className="text-sm font-bold text-emerald-800 animate-pulse">
                {t('chat.listening')}
              </span>
              <div className="flex gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-600 animate-bounce" />
                <span className="w-2 h-2 rounded-full bg-emerald-600 animate-bounce [animation-delay:0.2s]" />
                <span className="w-2 h-2 rounded-full bg-emerald-600 animate-bounce [animation-delay:0.4s]" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Suggestion Pills */}
      <div className="flex flex-wrap gap-2 py-2 flex-shrink-0">
        {quickPills.map((pill, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleSendMessage(pill)}
            disabled={loading}
            className="text-xs sm:text-sm font-semibold bg-emerald-50 hover:bg-emerald-100 text-emerald-900 border border-emerald-200 px-3 py-1.5 rounded-full transition-all active:scale-95 disabled:opacity-50 text-left cursor-pointer"
          >
            💡 {pill}
          </button>
        ))}
      </div>

      {/* Error Message */}
      <ErrorMessage error={error} onRetry={() => setError('')} className="my-1 py-2 flex-shrink-0" />

      {/* Input Form Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
        className="flex-shrink-0 pt-2"
      >
        <div className="flex items-center gap-2 bg-white rounded-3xl p-2 border-2 border-emerald-200 focus-within:border-emerald-600 shadow-sm transition-all">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder={t('chat.placeholder')}
            disabled={loading}
            className="flex-1 text-base sm:text-lg px-4 py-2 outline-none font-medium bg-transparent text-stone-900"
          />

          <button
            type="submit"
            disabled={loading || !inputMessage.trim()}
            className="h-12 w-12 sm:w-auto sm:px-6 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white font-extrabold rounded-2xl flex items-center justify-center gap-2 shadow-md active:scale-95 transition-all cursor-pointer"
          >
            <Send className="w-5 h-5" />
            <span className="hidden sm:inline">{t('chat.send_btn')}</span>
          </button>
        </div>

        {/* Small safety disclaimer */}
        <p className="text-[11px] sm:text-xs text-stone-600 text-center mt-2 flex items-center justify-center gap-1 font-medium">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
          <span>{t('chat.disclaimer')}</span>
        </p>
      </form>
    </div>
  );
};

export default Chat;
