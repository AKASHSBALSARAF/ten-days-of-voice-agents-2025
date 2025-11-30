'use client';

import React, { useLayoutEffect, useRef } from 'react';
import { motion, AnimatePresence, type HTMLMotionProps } from 'motion/react';
import { type ReceivedChatMessage } from '@livekit/components-react';
import { cn } from '@/lib/utils';

/**
 * Robust ChatTranscript:
 * - fixes variants typing error by passing `variants` explicitly and using `initial={false}` to avoid remount animation issues
 * - uses useLayoutEffect to scroll on new messages
 * - forces explicit, high-contrast text colors so theme variables won't hide text
 * - shows GM vs Player badges
 */

const containerVariants = {
  hidden: {
    opacity: 0,
  },
  visible: {
    opacity: 1,
    transition: {
      when: 'beforeChildren',
      staggerChildren: 0.06,
      delayChildren: 0.06,
    },
  },
};

const messageVariants = {
  hidden: { opacity: 0, translateY: 8 },
  visible: { opacity: 1, translateY: 0 },
};

function GmBadge() {
  return (
    <div className="h-9 w-9 rounded-full flex items-center justify-center bg-gradient-to-tr from-purple-500 to-purple-500 text-white shadow-sm">
      <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" aria-hidden>
        <circle cx="12" cy="12" r="4.2" stroke="currentColor" strokeWidth="1.2" />
        <path d="M2 12c3-4 10-6 20-6" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      </svg>
    </div>
  );
}

function PlayerBadge() {
  return (
    <div className="text-[11px] h-9 w-9 rounded-full flex items-center justify-center bg-purple-400 text-slate-700 font-bold shadow-sm">
      YOU
    </div>
  );
}

interface ChatTranscriptProps {
  hidden?: boolean;
  messages?: ReceivedChatMessage[];
  className?: string;
}

export function ChatTranscript({
  hidden = false,
  messages = [],
  className,
  ...props
}: ChatTranscriptProps & Omit<HTMLMotionProps<'div'>, 'ref'>) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  // reliable scroll-to-bottom after layout updates (useLayoutEffect => runs before paint)
  useLayoutEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    // small timeout is OK but useLayoutEffect ensures DOM sizes are ready
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, [messages?.length]);

  return (
    <AnimatePresence>
      {!hidden && (
        <motion.div
          // important: initial={false} prevents repeated 'hidden->visible' animation on remount,
          // but we still pass variants and animate so children animate in.
          initial={false}
          animate="visible"
          exit="hidden"
          variants={containerVariants as any}
          ref={containerRef}
          {...props}
          className={cn(
            'w-full max-h-[68vh] overflow-y-auto rounded-2xl p-4 shadow-lg',
            // background + padding chosen to work in dark & light with explicit text colors below
            'bg-[linear-gradient(180deg,#0f172a88,rgba(15,23,42,0.6))]',
            className
          )}
        >
          {/* header */}
          <div className="sticky top-0 z-10 mb-3 flex items-center gap-3 bg-black/20 py-2 px-3 rounded-xl backdrop-blur-sm">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 text-white font-semibold">
              GM
            </div>
            <div>
              <div className="text-sm font-semibold text-black-100">Lost in Space — Session</div>
              <div className="text-[11px] text-slate-400">Realtime voice transcript</div>
            </div>
          </div>

          <div className="space-y-3">
            {messages.map(({ id, timestamp, from, message, editTimestamp }: ReceivedChatMessage) => {
              const locale = (typeof navigator !== 'undefined' && navigator.language) || 'en-US';
              const messageOrigin = from?.isLocal ? 'local' : 'remote';
              const timeText = timestamp
                ? new Date(timestamp).toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' })
                : '';

              // Explicit colors so theme variables won't hide the text
              const bubbleClassLocal =
                'ml-auto bg-gradient-to-r from-purple-400/95 to-purple-300/95 text-slate-900';
              const bubbleClassRemote = 'mr-auto bg-slate-800/92 text-slate-100';

              return (
                <motion.div
                  key={id}
                  variants={messageVariants as any}
                  initial="hidden"
                  animate="visible"
                  exit="hidden"
                  className="flex items-end gap-3"
                  aria-live="polite"
                >
                  {/* GM / remote on left */}
                  {messageOrigin === 'remote' && (
                    <div className="flex-shrink-0">
                      <GmBadge />
                    </div>
                  )}

                  <div className={cn('max-w-[86%] break-words px-4 py-2 rounded-2xl text-sm leading-relaxed shadow-sm', messageOrigin === 'local' ? bubbleClassLocal : bubbleClassRemote)}>
                    <div className="whitespace-pre-wrap" style={{ color: messageOrigin === 'local' ? undefined : undefined }}>
                      {/* Render message as plain text. If it's not visible, it's likely CSS. */}
                      {String(message ?? '')}
                    </div>
                    <div className="mt-1 flex items-center justify-between gap-2">
                      <span className="text-[11px] text-slate-200/70">{timeText}</span>
                      {editTimestamp && <span className="text-[11px] italic text-slate-200/60">edited</span>}
                    </div>
                  </div>

                  {/* Player / local avatar right */}
                  {messageOrigin === 'local' && (
                    <div className="flex-shrink-0">
                      <PlayerBadge />
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default ChatTranscript;
