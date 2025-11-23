import logging
import json

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
    tokenize,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")


# -------------------------------
#  BARISTA ASSISTANT CLASS
# -------------------------------
class Assistant(Agent):
    def __init__(self):
        super().__init__(
            instructions="""
You are a friendly coffee shop barista.
Your job is to take the user's coffee order.
Ask questions until you fill all fields in the order:

drink type
size
milk preference
extras
customer name

After collecting a field, confirm briefly.
When the order is complete, say the summary.

Keep responses short and friendly.
"""
        )

        # Order state for the session
        self.order = {
            "drinkType": "",
            "size": "",
            "milk": "",
            "extras": [],
            "name": ""
        }

    def is_order_complete(self):
        return (
            self.order["drinkType"] != "" and
            self.order["size"] != "" and
            self.order["milk"] != "" and
            self.order["name"] != ""
        )

    def next_question(self):
        if not self.order["drinkType"]:
            return "What type of drink would you like?"
        if not self.order["size"]:
            return "What size would you prefer? Small, medium, or large?"
        if not self.order["milk"]:
            return "What kind of milk would you like?"
        if len(self.order["extras"]) == 0:
            return "Any extras like sugar, whipped cream, or caramel?"
        if not self.order["name"]:
            return "May I have your name for the order?"
        return None


# -------------------------------
#  PREWARM VAD
# -------------------------------
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


# -------------------------------
#  ENTRYPOINT
# -------------------------------
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    # Voice pipeline: STT + LLM + TTS
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),

        llm=google.LLM(
            model="gemini-2.5-flash",
        ),

        tts=murf.TTS(
            voice="en-US-matthew",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True
        ),

        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Start the barista session
    agent = Assistant()

    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # -------------------------------
    #  BARISTA ORDER LOGIC
    # -------------------------------
    @session.on("transcription")
    async def on_user_speaks(evt):
        user_text = evt.text.lower()

        # Fill order fields
        if not agent.order["drinkType"]:
            agent.order["drinkType"] = user_text

        elif not agent.order["size"]:
            agent.order["size"] = user_text

        elif not agent.order["milk"]:
            agent.order["milk"] = user_text

        elif len(agent.order["extras"]) == 0:
            if "no" in user_text:
                agent.order["extras"] = []
            else:
                agent.order["extras"] = [user_text]

        elif not agent.order["name"]:
            agent.order["name"] = user_text

        # Ask next question
        if not agent.is_order_complete():
            q = agent.next_question()
            await session.say(q)
            return

        # -------------------------------
        #  ORDER COMPLETE → SAVE & CONFIRM
        # -------------------------------
        summary = (
            f"Order confirmed. A {agent.order['size']} {agent.order['drinkType']} "
            f"with {agent.order['milk']} milk"
        )
        if agent.order["extras"]:
            summary += f" and extras: {', '.join(agent.order['extras'])}"
        summary += f" for {agent.order['name']}."

        await session.say(summary)

        # Save order to file
        with open("orders.json", "a") as f:
            json.dump(agent.order, f)
            f.write("\n")

        await session.say("Your order has been saved. Anything else?")

    # Connect user to agent
    await ctx.connect()


# -------------------------------
#  WORKER
# -------------------------------
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
