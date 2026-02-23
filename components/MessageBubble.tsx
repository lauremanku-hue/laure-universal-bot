import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Message, Role } from '../types';
import { User, Bot } from 'lucide-react';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === Role.USER;

  return (
    <div className={`flex w-full mb-6 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-[85%] md:max-w-[75%] gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-indigo-600 text-white' : 'bg-emerald-600 text-white'
        }`}>
          {isUser ? <User size={18} /> : <Bot size={18} />}
        </div>

        {/* Bubble */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          <div
            className={`px-4 py-3 rounded-2xl shadow-sm text-sm md:text-base leading-relaxed overflow-hidden ${
              isUser
                ? 'bg-indigo-600 text-white rounded-tr-sm'
                : 'bg-white border border-slate-200 text-slate-800 rounded-tl-sm'
            } ${message.isError ? 'bg-red-50 border-red-200 text-red-600' : ''}`}
          >
            {message.isError ? (
              <span>{message.content}</span>
            ) : (
              <div className={`markdown-content ${isUser ? 'text-white' : 'text-slate-800'}`}>
                <ReactMarkdown
                  components={{
                    code({ className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className || '')
                        const isInline = !match && !String(children).includes('\n');
                        
                        return isInline ? (
                            <code className={`${isUser ? 'bg-indigo-700' : 'bg-slate-100'} px-1 py-0.5 rounded font-mono text-xs`} {...props}>
                                {children}
                            </code>
                        ) : (
                            <div className="my-2 rounded-md overflow-hidden bg-slate-900 text-slate-50 p-3 text-xs font-mono overflow-x-auto">
                                <code className={className} {...props}>
                                    {children}
                                </code>
                            </div>
                        )
                    },
                    p({ children }) {
                        return <p className="mb-2 last:mb-0">{children}</p>
                    },
                    ul({ children }) {
                        return <ul className="list-disc ml-4 mb-2">{children}</ul>
                    },
                    ol({ children }) {
                        return <ol className="list-decimal ml-4 mb-2">{children}</ol>
                    },
                    a({ href, children }) {
                        return <a href={href} target="_blank" rel="noopener noreferrer" className="underline font-medium hover:opacity-80">{children}</a>
                    }
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </div>
          <span className="text-xs text-slate-400 mt-1 px-1">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>
    </div>
  );
};
