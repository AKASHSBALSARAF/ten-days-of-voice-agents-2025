# Day 9 – E‑Commerce Voice Agent (ACP‑Inspired)

This project implements a lightweight, voice‑driven shopping assistant following the core ideas of the Agentic Commerce Protocol (ACP).  
It runs entirely through the LiveKit Voice Agent (Python backend + Next.js frontend).

## ✅ Features Implemented
- Voice‑driven shopping: “show hoodies”, “list mugs”, “buy the black hoodie”
- ACP‑style merchant layer inside **agent.py**
- Product catalog stored **inside agent.py** (no external JSON)
- Filtering by:
  - category (hoodie, mug, tshirt)
  - price (e.g., “under 1500”)
  - color (“black hoodie”, “blue mug”)
- Ordering flow:
  - Understand user intent
  - Resolve matching product
  - Create order with product, quantity, size
  - Persist orders to `orders.json`
- Query last order: “What did I buy?”
- Fully voice‑controlled through the existing Day 1–Day 9 frontend

## 📁 Project Structure (Only What We Actually Implemented)
```
backend/
  ├── src/
  │     └── agent.py        # FULL ACP logic, product catalog, order tools
  ├── orders.json           # Created automatically when orders are placed
  └── .env.local
frontend/
  ├── components/
  │     └── app/
  │           ├── welcome-view.tsx   # Updated Day 9 UI
  │           ├── view-controller.tsx
  │           └── session-view.tsx
```

No external:  
❌ `products.json`  
❌ `store.py`  
We did **not** implement those — everything is inside **agent.py** exactly as you requested.

## ▶️ Running the Project

### 1. Install dependencies
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start LiveKit Agent
```bash
cd backend
python src/agent.py
```

You should see:
```
E‑Commerce Agent Ready – ACP Mini Layer Active
```

### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

Open:
```
http://localhost:3000
```

You will see the **Day 9 Welcome Screen**  
→ Click **Start Shopping**  
→ Speak naturally to the agent.

---

## 🎤 Supported Voice Queries

### Browsing Products
```
Show me all hoodies
List the coffee mugs
Do you have t‑shirts under 1000 rupees?
Any black hoodie available?
```

### Purchasing
```
I want to buy the black hoodie
Get the blue mug
I want 2 t-shirts size M
```

### Confirming Size
```
Buy the hoodie in size L
Order the t-shirt in medium
```

### Finalizing Order
```
That's all
Place my order
I’m done
```

The agent will:
- confirm the cart  
- generate an order object  
- save to `orders.json`  

### Checking Your Order
```
What did I buy?
Show my last order
```

---

## 🛒 How Orders Are Saved (orders.json)
Example:
```json
{
  "id": "order_0012",
  "items": [
    {
      "product_id": "hoodie-002",
      "name": "Classic Black Hoodie",
      "quantity": 1,
      "size": "L",
      "price": 1499,
      "currency": "INR"
    }
  ],
  "total": 1499,
  "currency": "INR",
  "created_at": "2025-02-15T12:31:45Z"
}
```

---

## 🛠 Notes
- No payment logic — ACP‑style simulated only.
- No database required — simple JSON persistence.
- Logic is fully voice‑driven using:
  - Deepgram STT  
  - Gemini LLM  
  - Murf TTS  
  - LiveKit turn detection

---

## 🎉 Day 9 Complete!
Your assistant now:
- interprets shopping intents  
- filters a product catalog  
- creates structured ACP‑style orders  
- persists them  
- retrieves previous orders  

Perfectly aligned with the Day 9 requirements.
