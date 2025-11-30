import logging
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

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
    function_tool,
    RunContext,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")
load_dotenv(".env.local")

DEFAULT_VOICE = "en-US-matthew"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDERS_DIR = os.path.join(BASE_DIR, "orders")
ORDERS_FILE = os.path.join(ORDERS_DIR, "day9_orders.json")

# -------------------------------------------------------------------
#  CATALOG (in-code, ACP-style structure)
# -------------------------------------------------------------------

CATALOG: List[Dict[str, Any]] = [
    {
        "id": "mug-001",
        "name": "Stoneware Coffee Mug",
        "description": "Sturdy stoneware coffee mug with a matte finish.",
        "price": 799,
        "currency": "INR",
        "category": "mug",
        "color": "white",
    },
    {
        "id": "mug-002",
        "name": "Blue Ceramic Mug",
        "description": "Glossy blue ceramic mug, 350ml.",
        "price": 599,
        "currency": "INR",
        "category": "mug",
        "color": "blue",
    },
    {
        "id": "tee-001",
        "name": "Minimal Logo T-Shirt",
        "description": "Black cotton tee with a small chest logo.",
        "price": 899,
        "currency": "INR",
        "category": "tshirt",
        "color": "black",
        "sizes": ["S", "M", "L", "XL"],
    },
    {
        "id": "tee-002",
        "name": "Graphic T-Shirt",
        "description": "White t-shirt with a subtle abstract graphic.",
        "price": 1099,
        "currency": "INR",
        "category": "tshirt",
        "color": "white",
        "sizes": ["M", "L"],
    },
    {
        "id": "hood-001",
        "name": "Classic Black Hoodie",
        "description": "Soft fleece hoodie with kangaroo pocket.",
        "price": 1599,
        "currency": "INR",
        "category": "hoodie",
        "color": "black",
        "sizes": ["S","M", "L", "XL"],
    },
    {
        "id": "hood-002",
        "name": "Olive Green Hoodie",
        "description": "Lightweight hoodie, perfect for layering.",
        "price": 1399,
        "currency": "INR",
        "category": "hoodie",
        "color": "green",
        "sizes": ["S", "M", "L"],
    },
    {
        "id": "acc-001",
        "name": "Canvas Tote Bag",
        "description": "Reusable off-white canvas tote bag.",
        "price": 499,
        "currency": "INR",
        "category": "accessory",
        "color": "beige",
    },
    {
        "id": "acc-002",
        "name": "Black Baseball Cap",
        "description": "Adjustable cap with curved visor.",
        "price": 699,
        "currency": "INR",
        "category": "accessory",
        "color": "black",
    },
]

ORDERS: List[Dict[str, Any]] = []


# -------------------------------------------------------------------
#  Helpers: load/save orders, normalize categories, filter products
# -------------------------------------------------------------------

def _ensure_orders_loaded() -> None:
    """Load existing orders from JSON (if any) into ORDERS."""
    global ORDERS
    try:
        # Ensure orders directory exists
        os.makedirs(ORDERS_DIR, exist_ok=True)
        
        if not os.path.exists(ORDERS_FILE):
            logger.info("No existing orders file found at %s, starting fresh", ORDERS_FILE)
            ORDERS = []
            return
            
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if isinstance(data, list):
            ORDERS = data
            logger.info("Loaded %d existing orders from %s", len(ORDERS), ORDERS_FILE)
        else:
            logger.warning("Orders file contains invalid data, starting fresh")
            ORDERS = []
            
    except json.JSONDecodeError:
        logger.exception("Invalid JSON in orders file, starting fresh")
        ORDERS = []
    except Exception as e:
        logger.exception("Failed to load existing orders; starting fresh. Error: %s", str(e))
        ORDERS = []


def _persist_orders() -> None:
    """Write ORDERS list to JSON atomically."""
    try:
        os.makedirs(ORDERS_DIR, exist_ok=True)
        tmp = ORDERS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(ORDERS, f, indent=2, ensure_ascii=False, default=str)
        os.replace(tmp, ORDERS_FILE)
        logger.info("Persisted %d orders to %s", len(ORDERS), ORDERS_FILE)
    except Exception as e:
        logger.error("Failed to persist orders: %s", str(e))
        raise


def _normalize_category(raw: Optional[str]) -> Optional[str]:
    """Map 'hoodies', 't-shirts', 'tees', 'mugs', etc. into stable keys."""
    if not raw:
        return None
    s = raw.strip().lower()
    s = s.replace("-", "").replace(" ", "")
    if s.endswith("s"):
        s = s[:-1]

    mapping = {
        "mug": "mug",
        "coffee": "mug",
        "coffeemug": "mug",
        "cup": "mug",
        "tshirt": "tshirt",
        "tee": "tshirt",
        "shirt": "tshirt",
        "hoodie": "hoodie",
        "hood": "hoodie",
        "sweatshirt": "hoodie",
        "jumper": "hoodie",
        "accessory": "accessory",
        "cap": "accessory",
        "hat": "accessory",
        "bag": "accessory",
        "tote": "accessory",
    }
    return mapping.get(s, s)


def _filter_products(
    category: Optional[str] = None,
    max_price: Optional[int] = None,
    color: Optional[str] = None,
    text_query: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Lenient filtering:
      - category / color are normalized and treated as soft filters.
      - text_query checks name+description.
      - if filters yield 0, we fall back to full catalog.
    """
    cat_norm = _normalize_category(category)
    color_norm = color.strip().lower() if color else None
    text_norm = text_query.strip().lower() if text_query else None

    results: List[Dict[str, Any]] = []

    for p in CATALOG:
        # max price is hard filter
        if max_price is not None and p.get("price", 0) > max_price:
            continue

        pc = _normalize_category(p.get("category"))
        if cat_norm and pc != cat_norm:
            continue

        if color_norm:
            pc_color = str(p.get("color", "")).lower()
            if color_norm not in pc_color:
                continue

        if text_norm:
            blob = (p.get("name", "") + " " + p.get("description", "")).lower()
            if text_norm not in blob:
                continue

        results.append(p)

    # If filters applied but nothing found, fall back to entire catalog
    if not results and (cat_norm or max_price is not None or color_norm or text_norm):
        logger.info(
            "Filters matched no products (category=%r, max_price=%r, color=%r, text=%r). "
            "Falling back to full catalog.",
            cat_norm,
            max_price,
            color_norm,
            text_norm,
        )
        return CATALOG.copy()

    # No filters means return all
    if not results and not (cat_norm or max_price is not None or color_norm or text_norm):
        return CATALOG.copy()

    return results


def _find_product_by_id(pid: str) -> Optional[Dict[str, Any]]:
    for p in CATALOG:
        if p.get("id") == pid:
            return p
    return None


# -------------------------------------------------------------------
#  Agent
# -------------------------------------------------------------------

class CommerceAgent(Agent):
    """
    Voice shopping assistant with ACP-style separation:
    - Conversation handled by LLM + voice.
    - Catalog + orders handled by Python tools.
    """

    def __init__(self) -> None:
        super().__init__(
            instructions="""
You are a calm, reliable voice shopping assistant for a fictional online store.

You follow an Agentic Commerce style:
- You handle conversation in natural language.
- You use tools to browse the catalog and create orders.
- You NEVER invent products, ids, or prices. Only use tool results.

CATALOG:
- Products include mugs, t-shirts, hoodies, and accessories.
- Each product has id, name, price, currency, category, color, and sometimes sizes.

WHEN USER WANTS TO BROWSE OR CHECK AVAILABILITY:
- If the user asks things like:
  - "Any hoodies available?"
  - "Show me mugs."
  - "Do you have a blue mug?"
  - "T-shirts under 1000 rupees."
  - "What products do you have?"
  you MUST call the tool `list_products` with simple filters:
    - category: a short word like "hoodie", "mug", "tshirt", "accessory" if you can infer it.
    - max_price: integer if they mention a budget.
    - color: if they mention color.
    - text_query: if they say something like "coffee mug" or "minimal logo".
- After calling `list_products`, ALWAYS read out a few items with numbering:
  Example:
    "I found 2 hoodies. (1) Classic Black Hoodie for 1599 rupees. (2) Olive Green Hoodie for 1399 rupees."
- If `count` is 0, you can say "I could not find an exact match, but here are some other items in the store"
  and then call `list_products` again with fewer or no filters.
- Never claim the store is completely empty, because the catalog is always available.

WHEN USER WANTS TO BUY:
- If the user says things like:
  - "I'll buy the second hoodie."
  - "Get me that blue mug."
  - "Buy the first t-shirt in size M."
- Use recent tool results and your own reasoning to pick the product id.
- Then call `create_order` with:
    product_id: chosen product id
    quantity: default 1 unless they clearly say 2 or more
    size: pass a size like "S", "M", "L", "XL" if the product has sizes and the user mentions one.
- After the tool returns, confirm:
  - product name
  - size (if any)
  - quantity
  - total price in rupees
  - order id

LAST ORDER:
- If the user asks "What did I just buy?" or "What was my last order?",
  call `get_last_order` and summarize the latest order.

STYLE:
- Short, clear, friendly.
- Mention prices in "rupees" or "INR".
- This is a demo: never talk about real payment, delivery address, or refunds.
"""
        )
        _ensure_orders_loaded()

    # -------------------- Tools --------------------

    @function_tool
    async def list_products(
        self,
        context: RunContext,
        category: Optional[str] = None,
        max_price: Optional[int] = None,
        color: Optional[str] = None,
        text_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Browse the product catalog using lenient filters.

        Args:
            category: words like "mug", "tshirt", "hoodie", "accessory" or related.
            max_price: max price in INR.
            color: e.g. "black", "blue".
            text_query: keyword filter over name/description, e.g. "coffee", "logo".

        Returns:
            {
              "count": int,
              "products": [...product dicts...]
            }
        """
        products = _filter_products(
            category=category,
            max_price=max_price,
            color=color,
            text_query=text_query,
        )
        logger.info(
            "list_products called with category=%r, max_price=%r, color=%r, text=%r -> %d results",
            category,
            max_price,
            color,
            text_query,
            len(products),
        )
        return {"count": len(products), "products": products}

    @function_tool
    async def create_order(
        self,
        context: RunContext,
        product_id: str,
        quantity: int = 1,
        size: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an order for a single product.

        Args:
            product_id: id of the product to buy.
            quantity: how many units (min 1).
            size: optional size for wearables, e.g. "S", "M", "L", "XL".

        Returns:
            {
              "ok": bool,
              "order": { ... }  # if ok is True
            }
        """
        product = _find_product_by_id(product_id)
        if product is None:
            logger.warning("create_order called with unknown product_id=%r", product_id)
            return {"ok": False, "error": f"Unknown product id {product_id!r}"}

        quantity = max(1, quantity)
        order_id = f"ORD-{int(datetime.now(timezone.utc).timestamp())}"
        line_total = product["price"] * quantity

        item: Dict[str, Any] = {
            "product_id": product["id"],
            "name": product["name"],
            "quantity": quantity,
            "unit_price": product["price"],
        }
        if size:
            item["size"] = size

        order: Dict[str, Any] = {
            "id": order_id,
            "items": [item],
            "total": line_total,
            "currency": product.get("currency", "INR"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        ORDERS.append(order)
        _persist_orders()

        logger.info(
            "Created order %s for product %s x%d (size=%r, total=%d)",
            order_id,
            product["id"],
            quantity,
            size,
            line_total,
        )

        return {"ok": True, "order": order}

    @function_tool
    async def get_last_order(self, context: RunContext) -> Dict[str, Any]:
        """
        Return the most recent order placed in this system.
        """
        if not ORDERS:
            return {"ok": False, "message": "No orders have been placed yet."}
        return {"ok": True, "order": ORDERS[-1]}


# -------------------------------------------------------------------
#  LiveKit wiring
# -------------------------------------------------------------------

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    agent = CommerceAgent()

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(
            voice=DEFAULT_VOICE,
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    logger.info("Day 9 CommerceAgent ready (ACP-lite, categories+sizes fixed).")

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))