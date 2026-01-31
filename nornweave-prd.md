# **Product Requirement Document: NornWeave**

## **1. Executive Summary**

**Product Name:** NornWeave
**Vision:** An open-source, self-hosted API that turns standard email providers (Mailgun, SES, SendGrid) into "Inbox-as-a-Service" for AI Agents.
**Core Value:** Standard email APIs are stateless and built for transactional sending. NornWeave adds a **stateful layer** (Inboxes, Threads, History) and an **intelligent layer** (Markdown parsing, Semantic Search) to make email consumable by LLMs via REST or MCP.

## **2. System Architecture & Concepts**

To ensure flexibility, the system relies on two critical abstraction layers:

### **A. Storage Adapter Layer**

The system must not be hardcoded to PostgreSQL. It uses a `StorageInterface` to persist data.

* **Core Entities:** `Inbox`, `Thread`, `Message`, `Event`.
* **Initial Implementation:** `PostgresAdapter` (using raw SQL or an ORM like Prisma/SQLAlchemy).
* **Future Implementations:** `SQLiteAdapter` (for local dev), `MongoAdapter`.

### **B. Provider Adapter Layer (The "BYOP" Model)**

The system abstracts the underlying sending/receiving mechanism.

* **Interface:** `EmailProvider`
* `send_email(to, subject, body, headers)`
* `parse_inbound_webhook(request)` → Returns standardized `InboundMessage` object.
* `setup_inbound_route(inbox_address)` (Optional: auto-configure routes via provider API).


* **Supported Providers:** Mailgun, AWS SES, SendGrid, Resend.

---

## **3. Implementation Phases**

### **Phase 1: Foundation (The "Mail Proxy")**

*Goal: Create inboxes, receive emails via webhook, store them, and send replies.*

* **Features:**
* **Inboxes:** Create virtual inboxes (e.g., `support-bot@app.com`).
* **Ingestion:** Webhook endpoint to receive JSON from SendGrid/Mailgun.
* **Storage:** Save raw email + basic metadata in PostgreSQL.
* **Sending:** Passthrough sending via the configured provider.
* **Security:** Basic API Key authentication.



### **Phase 2: Intelligence & Protocol (The "Agent Layer")**

*Goal: Make email understandable for LLMs and connect via MCP.*

* **Features:**
* **Content Parsing:** Convert HTML → Markdown. Remove "Reply" cruft (e.g., "On Jan 1... wrote:").
* **Threading:** Logic to group messages into `Threads` based on `References` and `In-Reply-To` headers.
* **MCP Server:** Expose `read_inbox`, `send_reply` as MCP Tools for Claude/Cursor.
* **Attachments:** Extract text from PDFs/CSVs (basic OCR/parsing).



### **Phase 3: Advanced Platform (The "Enterprise Layer")**

*Goal: Feature parity with paid SaaS tools.*

* **Features:**
* **Semantic Search:** Vector embeddings for messages to allow queries like "Find the invoice from last week."
* **Real-time Webhooks:** Agents register a URL to get notified of new messages (`POST /my-agent-webhook`).
* **Multi-Tenancy:** "Organizations" and "Projects" to isolate data.
* **Custom Domains:** Logic to handle DKIM/SPF verification status.



---

## **4. API Specification (REST)**

### **A. Inboxes**

* `POST /v1/inboxes`
* **Body:** `{ "name": "Support Agent", "email_username": "support" }`
* **Result:** Creates a mapping in the DB. If using Mailgun/SES, creates the routing rule dynamically if permitted.


* `GET /v1/inboxes/{inbox_id}`
* `DELETE /v1/inboxes/{inbox_id}`

### **B. Threads (The LLM Context Unit)**

* `GET /v1/threads/{thread_id}`
* **Returns:** A Markdown-formatted conversation history optimized for context windows.
* **Example Response:**
```json
{
  "id": "th_123",
  "subject": "Re: Pricing Question",
  "messages": [
    { "role": "user", "author": "bob@gmail.com", "content": "How much is it?", "timestamp": "..." },
    { "role": "assistant", "author": "agent@myco.com", "content": "$20/mo", "timestamp": "..." }
  ]
}

```

### **C. Messages**

* `POST /v1/messages` (Send)
* **Body:**
```json
{
  "inbox_id": "ibx_555",
  "to": ["client@gmail.com"],
  "reply_to_thread_id": "th_123", // Optional: Handles threading headers auto-magically
  "subject": "Hello",
  "body": "Markdown content here..."
}

```




* `GET /v1/messages/{message_id}` (Retrieve Raw/Parsed)

### **D. Search**

* `POST /v1/search`
* **Body:** `{ "query": "invoices from October", "inbox_id": "..." }`
* **Implementation:** Uses basic SQL `ILIKE` (Phase 1) or Vector Search (Phase 3).



---

## **5. MCP Server Specification (Model Context Protocol)**

This server allows local LLMs (Cursor, Claude Desktop) to "plug in" to the email server.

### **Resources (Read-Only Context)**

* `email://inbox/{id}/recent` → List of last 10 threads summaries.
* `email://thread/{id}` → Full thread content in Markdown.

### **Tools (Executable Actions)**

1. **`create_inbox`**:
* Args: `name` (string), `username` (string).
* Desc: Provisions a new email address for the agent to use.


2. **`send_email`**:
* Args: `recipient`, `subject`, `body`, `thread_id` (optional).
* Desc: Sends an email. Automatically converts Markdown to HTML.


3. **`search_email`**:
* Args: `query`, `limit`.
* Desc: Finds relevant info in the inbox.


4. **`wait_for_reply`** (Long-polling / Experimental):
* Args: `thread_id`, `timeout_seconds`.
* Desc: Blocks execution until a new email arrives in the thread (useful for synchronous agent scripts).



---

## **6. Database Schema (Abstracted)**

Although implemented in SQL, the `StorageAdapter` must enforce this schema logic.

**Table: Inboxes**

* `id` (UUID)
* `email_address` (unique)
* `provider_config` (JSON) - Stores provider-specific metadata (e.g., Mailgun Route ID).

**Table: Threads**

* `id` (UUID)
* `inbox_id` (FK)
* `subject` (Text)
* `last_message_at` (Timestamp)
* `participant_hash` (String) - Unique hash of participants to help group loose emails.

**Table: Messages**

* `id` (UUID)
* `thread_id` (FK)
* `inbox_id` (FK)
* `provider_message_id` (String) - The Message-ID header from the email network.
* `direction` (Enum: INBOUND, OUTBOUND)
* `content_raw` (Text) - Original HTML/Text.
* `content_clean` (Text) - LLM-ready Markdown.
* `metadata` (JSON) - Headers, token counts, sentiment score (Phase 2).

---

## **7. Thematic Architecture Components**

To maintain the theme without sacrificing clarity, the architecture uses the following nomenclature:

| Technical Component | NornWeave Name | Thematic Reasoning |
| --- | --- | --- |
| **Database / Storage** | **Urðr (The Well)** | Urðr represents "The Past." The database holds the immutable history of what has already happened (logs, stored messages). |
| **Ingestion Engine** | **Verðandi (The Loom)** | Verðandi represents "The Present" or "Becoming." This engine processes incoming webhooks in real-time, parsing raw HTML into clean Markdown "threads." |
| **API & Outbound** | **Skuld (The Prophecy)** | Skuld represents "The Future" or "Debt." This layer handles what *shall be* done: sending emails, scheduling replies, and managing API credits/rate limits. |
| **API Gateway/Router** | **Yggdrasil** | The central axis that connects all disparate worlds (Email Providers like Mailgun, SES) into one unified structure. |
| **Monitoring / MCP Tools** | **Huginn & Muninn** | Odin’s ravens (Thought and Memory). These are the specific MCP tools (`search_inbox`, `fetch_thread`) that fly out to retrieve knowledge for the Agent. |


## **8. Open Source "Getting Started" Flow**

1. **Clone & Config:** User clones repo, copies `.env.example` to `.env`.
2. **Select Adapter:**
* `DB_DRIVER=postgres`
* `EMAIL_PROVIDER=mailgun`


3. **Set Keys:** User enters `MAILGUN_API_KEY` and `POSTGRES_CONNECTION_STRING`.
4. **Run:** `docker-compose up`.
5. **Configure Webhook:** User takes the URL `http://their-server.com/webhooks/mailgun` and pastes it into Mailgun's dashboard (or runs a setup script to do it automatically).

## **Project Identity and Landing Page: NornWeave**

**Origin & Concept**
In Norse mythology, the Norns (Urðr, Verðandi, and Skuld) dwell at the base of Yggdrasil, the World Tree. They draw water from the Well of Urðr to nourish the tree and prevent it from rotting, while simultaneously weaving the tapestry of fate for all beings.

**Relation to Software:**
Email is often a chaotic, rotting mess of raw HTML and disconnected messages. **NornWeave** acts as the Norns for AI Agents:

* It takes the raw "water" (incoming data streams).
* It "weaves" disconnected messages into coherent **Threads** (the Tapestry).
* It nourishes the Agent (Yggdrasil) with clean, structured context so it can survive and function at the center of the user's workflow.

**Quote for Homepage**

> *"Þær lög lögðu, þær líf völdu..."*
> "Laws they made there, and life allotted / To the sons of men, and set their fates."
> — *Völuspá (The Prophecy of the Seeress), Poetic Edda, Stanza 20.*

Place on the landing page the image @Nornorna_spinner.jpg and the following credits in small letters:

By L. B. Hansen - https://boudicca.de/gmedia-album/fredrik-sander-skaldeverk-edda-en/, Public Domain, https://commons.wikimedia.org/w/index.php?curid=164065