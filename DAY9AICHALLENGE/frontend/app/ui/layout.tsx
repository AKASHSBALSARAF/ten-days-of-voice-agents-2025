import * as React from 'react';
import { headers } from 'next/headers';
import { SessionProvider } from '@/components/app/session-provider';
import { getAppConfig } from '@/lib/utils';

export default async function ComponentsLayout({ children }: { children: React.ReactNode }) {
  const hdrs = await headers();
  const appConfig = await getAppConfig(hdrs);

  return (
    <SessionProvider appConfig={appConfig}>
      <div className="min-h-svh p-8 bg-[#fdf7f2]"> 
        {/* Light creamy coffee background */}
        <div className="mx-auto max-w-3xl space-y-8">
          <header className="space-y-3">
            <h1 className="text-5xl font-extrabold tracking-tight text-[#7b2e2f] drop-shadow-sm">
              Café Delight ☕
            </h1>

            <p className="text-[#5a3b38] max-w-80 leading-tight text-pretty">
              Welcome to our cozy Café Coffee Day–inspired space. 
              Your friendly barista AI is here to take your order!
            </p>

            <p className="text-[#6d4c41] max-w-prose text-balance">
              Powered by{' '}
              <a href="https://livekit.io" className="underline underline-offset-2 decoration-[#7b2e2f]">
                LiveKit
              </a>
              , served with a sprinkle of love. 💗
            </p>
          </header>

          <main className="space-y-20 bg-white/70 backdrop-blur-md shadow-xl rounded-2xl p-6 border border-[#e6d6c9]">
            {children}
          </main>
        </div>
      </div>
    </SessionProvider>
  );
}
