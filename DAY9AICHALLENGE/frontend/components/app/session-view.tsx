'use client';

import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'motion/react';
import type { AppConfig } from '@/app-config';
import { ChatTranscript } from '@/components/app/chat-transcript';
import { PreConnectMessage } from '@/components/app/preconnect-message';
import { TileLayout } from '@/components/app/tile-layout';
import {
  AgentControlBar,
  type ControlBarControls,
} from '@/components/livekit/agent-control-bar/agent-control-bar';
import { useChatMessages } from '@/hooks/useChatMessages';
import { useConnectionTimeout } from '@/hooks/useConnectionTimout';
import { useDebugMode } from '@/hooks/useDebug';
import { cn } from '@/lib/utils';
import { ScrollArea } from '../livekit/scroll-area/scroll-area';

const MotionBottom = motion.create('div');

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';
const BOTTOM_VIEW_MOTION_PROPS = {
  variants: {
    visible: { opacity: 1, translateY: '0%' },
    hidden: { opacity: 0, translateY: '100%' },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: { duration: 0.3, delay: 0.5, ease: 'easeOut' },
};

export function Fade({ top = false, bottom = false, className }: {
  top?: boolean;
  bottom?: boolean;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'pointer-events-none h-4 bg-linear-to-b from-transparent to-transparent',
        top && 'from-[#FBE9D0] to-transparent',
        bottom && 'from-transparent to-[#FBE9D0]',
        className
      )}
    />
  );
}

interface SessionViewProps {
  appConfig: AppConfig;
}

export const SessionView = ({
  appConfig,
  ...props
}: React.ComponentProps<'section'> & SessionViewProps) => {
  useConnectionTimeout(200_000);
  useDebugMode({ enabled: IN_DEVELOPMENT });

  const messages = useChatMessages();
  const [chatOpen, setChatOpen] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const controls: ControlBarControls = {
    leave: true,
    microphone: true,
    chat: appConfig.supportsChatInput,
    camera: appConfig.supportsVideoInput,
    screenShare: appConfig.supportsVideoInput,
  };

  useEffect(() => {
    const lastMessage = messages.at(-1);
    if (scrollAreaRef.current && lastMessage?.from?.isLocal) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <section
      className={cn(
        'relative z-10 h-full w-full overflow-hidden',
        // CCD Background Theme
        'bg-[radial-gradient(circle_at_top,#FBE9D0_0%,#F7D7C1_45%,#F3C5A8_100%)]'
      )}
      {...props}
    >
      {/* Coffee Steam Top Glow */}
      <div className="absolute top-0 inset-x-0 h-20 bg-gradient-to-b from-[#E31837]/40 to-transparent pointer-events-none" />

      {/* Chat Transcript */}
      <div
        className={cn(
          'fixed inset-0 grid grid-cols-1 grid-rows-1',
          !chatOpen && 'pointer-events-none'
        )}
      >
        <Fade top className="absolute inset-x-4 top-0 h-40" />

        <ScrollArea
          ref={scrollAreaRef}
          className="px-4 pt-40 pb-[150px] md:px-6 md:pb-[180px]"
        >
          <ChatTranscript
            hidden={!chatOpen}
            messages={messages}
            className={cn(
              'mx-auto max-w-2xl space-y-3 transition-opacity duration-300 ease-out',
              // Café-style bubbles
              '[&>*]:rounded-2xl [&>*]:px-4 [&>*]:py-3',
              '[&>*]:shadow-md',
              '[&>*:not(.local)]:bg-white/90',
              '[&>.local]:bg-[#E31837]/90 [&>.local]:text-white'
            )}
          />
        </ScrollArea>
      </div>

      {/* Tiles (Avatar, waveform, etc.) */}
      <TileLayout chatOpen={chatOpen} />

      {/* Bottom Control Bar */}
      <MotionBottom
        {...BOTTOM_VIEW_MOTION_PROPS}
        className="fixed inset-x-3 bottom-0 z-50 md:inset-x-12"
      >
        {appConfig.isPreConnectBufferEnabled && (
          <PreConnectMessage messages={messages} className="pb-4" />
        )}

        <div className="relative mx-auto max-w-2xl pb-3 md:pb-12">
          <Fade bottom className="absolute inset-x-0 top-0 h-4 -translate-y-full" />

          <AgentControlBar
            controls={controls}
            onChatOpenChange={setChatOpen}
            className={cn(
              'rounded-2xl bg-white/80 shadow-xl backdrop-blur-md',
              'border border-[#E31837]/20'
            )}
          />
        </div>
      </MotionBottom>
    </section>
  );
};
