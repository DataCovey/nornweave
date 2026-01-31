## **1. Thematic Architecture Components**

To maintain the theme without sacrificing clarity, the architecture uses the following nomenclature:

| Technical Component | NornWeave Name | Thematic Reasoning |
| --- | --- | --- |
| **Database / Storage** | **Urðr (The Well)** | Urðr represents "The Past." The database holds the immutable history of what has already happened (logs, stored messages). |
| **Ingestion Engine** | **Verðandi (The Loom)** | Verðandi represents "The Present" or "Becoming." This engine processes incoming webhooks in real-time, parsing raw HTML into clean Markdown "threads." |
| **API & Outbound** | **Skuld (The Prophecy)** | Skuld represents "The Future" or "Debt." This layer handles what *shall be* done: sending emails, scheduling replies, and managing API credits/rate limits. |
| **API Gateway/Router** | **Yggdrasil** | The central axis that connects all disparate worlds (Email Providers like Mailgun, SES) into one unified structure. |
| **Monitoring / MCP Tools** | **Huginn & Muninn** | Odin’s ravens (Thought and Memory). These are the specific MCP tools (`search_inbox`, `fetch_thread`) that fly out to retrieve knowledge for the Agent. |

---

#### **Phase 1: The Well & The Loom (Foundation)**

*Goal: Establish the storage (Urðr) and the ingestion engine (Verðandi) to receive and store mail.*

**A. Core Features**

1. **Provider Agnostic Router (Yggdrasil)**
* **Adapter Interface:** Create a standardized Python interface `EmailProvider` with methods `parse_webhook` and `send_raw`.
* **Initial Adapters:** Implement `MailgunAdapter` and `SESAdapter`.
* **Configuration:** allow users to switch providers via simple ENV variables (e.g., `PROVIDER=mailgun`).


2. **The Well (Storage Layer)**
* **Abstracted Storage:** Use SQLAlchemy or Prisma to support SQLite (local dev) and PostgreSQL (production).
* **Schema - `Inboxes`:** Stores `id`, `email_address`, `provider_config`.
* **Schema - `Messages`:** Stores raw MIME data (for fidelity) and parsed text (for agents).


3. **The Loom (Ingestion Logic)**
* **Webhook Endpoint:** `POST /webhooks/ingest`.
* **Sanitization:** Convert incoming HTML to Markdown using `html2text`.
* **Cruft Removal:** Strip "On [Date], User wrote..." signatures to save LLM tokens.



**B. Deliverable Endpoints**

* `POST /v1/inboxes` (Create a new receiver address).
* `GET /v1/inboxes/{id}/messages` (Read raw history).

---

#### **Phase 2: The Tapestry & The Ravens (Agent Integration)**

*Goal: Implement the threading logic and the MCP Server so agents can "fly" and fetch data.*

**A. Core Features**

1. **Thread Weaving**
* **Logic:** Group messages based on standard headers (`References`, `In-Reply-To`) and Subject line fuzzy matching.
* **Context Window Optimization:** Create a "Summary View" that truncates old quoted text from the thread history, ensuring the LLM only reads unique content.


2. **Huginn (MCP Read Tools)**
* Expose an MCP Server (Model Context Protocol) compatible with Cursor/Claude.
* **Resource:** `email://inbox/{id}/recent` (List recent threads).
* **Resource:** `email://thread/{id}` (Render full thread as Markdown).


3. **Muninn (MCP Write Tools)**
* **Tool:** `reply_to_thread(thread_id, body)`
* Automatically resolves the `Reply-To` and `References` headers so the email threads correctly in Gmail/Outlook.





**B. Deliverable**

* A running `nornweave-mcp` server.
* Agents can now "chat" with their inbox: *"Check if I received the invoice from client X."*

---

#### **Phase 3: Skuld (Control & Future)**

*Goal: Rate limiting, semantic search, and enterprise controls.*

**A. Core Features**

1. **Rate Limiting (Skuld’s Debt)**
* Implement token bucket algorithms to prevent Agents from spamming (e.g., Max 5 replies/minute).
* **Cost Control:** Track and limit attachment sizes.


2. **Semantic Search (Wisdom)**
* Add a vector column to the `Messages` table (using `pgvector`).
* Embed incoming emails upon receipt.
* **Tool:** `search_knowledge_base(query)` allowing agents to ask abstract questions like "What was the tone of the negotiation last week?"


3. **Webhooks (Outbound Prophecy)**
* Allow external apps to subscribe to NornWeave events (`thread.new_message`).


