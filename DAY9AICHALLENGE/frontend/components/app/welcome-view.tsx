"use client";

import React from "react";
import { Button } from "@/components/livekit/button";

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ...props
}: React.ComponentProps<"div"> & WelcomeViewProps) => {
  return (
    <div
      {...props}
      className="min-h-screen w-full px-6 py-10 flex flex-col items-center justify-center 
                 bg-gradient-to-br from-indigo-900 via-slate-900 to-black text-slate-100"
    >
      {/* Header */}
      <div className="text-center space-y-3 max-w-2xl">
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
          Your AI Voice Shopping Assistant
        </h1>

        <p className="text-slate-300 text-sm md:text-base leading-relaxed">
          Browse products, compare prices, and place orders — all through natural conversation.  
          Powered by a lite Agentic Commerce Protocol workflow.
        </p>
      </div>

      {/* 3 Feature Blocks */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-10 max-w-4xl w-full">
        {/* Feature #1 */}
        <div className="bg-slate-800/50 backdrop-blur rounded-2xl p-5 border border-slate-700 shadow-lg">
          <h2 className="text-lg font-semibold mb-1">Browse by Voice</h2>
          <p className="text-xs text-slate-300 mb-2">
            Search for products by price, category, color, or size.
          </p>
          <p className="text-[11px] text-indigo-400">
            Try: “Show me hoodies under 1500.”
          </p>
        </div>

        {/* Feature #2 */}
        <div className="bg-slate-800/50 backdrop-blur rounded-2xl p-5 border border-slate-700 shadow-lg">
          <h2 className="text-lg font-semibold mb-1">Place an Order</h2>
          <p className="text-xs text-slate-300 mb-2">
            Pick any product you hear about. I’ll create a structured order object with pricing.
          </p>
          <p className="text-[11px] text-indigo-400">
            Try: “Buy the second mug you mentioned.”
          </p>
        </div>

        {/* Feature #3 */}
        <div className="bg-slate-800/50 backdrop-blur rounded-2xl p-5 border border-slate-700 shadow-lg">
          <h2 className="text-lg font-semibold mb-1">Review Your Order</h2>
          <p className="text-xs text-slate-300 mb-2">
            Ask about your latest order and I’ll fetch the stored JSON summary.
          </p>
          <p className="text-[11px] text-indigo-400">
            Try: “What did I buy just now?”
          </p>
        </div>
      </div>

      {/* CTA */}
      <Button
        size="lg"
        className="mt-10 px-10 py-4 rounded-2xl font-medium 
                   bg-indigo-500 hover:bg-indigo-600 text-black shadow-lg"
        onClick={onStartCall}
      >
        {startButtonText || "Start Shopping"}
      </Button>

      <p className="mt-4 text-[11px] text-slate-500">
        Demo Only · No Real Payments · Orders Saved as JSON
      </p>
    </div>
  );
};

export default WelcomeView;