# 📧 Email MCP Agent

A Streamlit app that gives AI agents their own email addresses using [NornWeave](https://github.com/DataCovey/nornweave) and the Model Context Protocol (MCP). Built around **real use cases** — support triage, task coordination, and inbox automation — with a self-contained tutorial you can run end-to-end.

---

## When would you use this?

Email-powered agents make sense when the **workflow** is the product:

- **Support inbox assistant** — Monitor a shared support address, triage by topic, and draft replies (or escalate) so humans only approve and send.
- **Task coordination via email** — An agent that owns an address like `tasks@yourdomain.com`: receives requests, parses them into tasks, and keeps a thread-based paper trail with stakeholders.
- **Stakeholder updates** — Digest internal events or reports and send summary emails to a list; replies can feed back into the agent for follow-up.

This app focuses on the **support inbox** scenario. The tutorial below covers the core loop (create inbox, seed tickets, triage, search, draft reply). [Advanced](#advanced) covers attachments, batch processing, and wait-for-reply.

---

## Tutorial: Support inbox assistant

**Goal:** Build a working support-agent loop — create an inbox, receive tickets, triage by topic, and draft replies. Five steps; demo mode needs no email provider or `.env`.

**What you'll need:** Python 3.10+, OpenAI API key.

### Step 1: Run NornWeave (demo mode)

Demo mode gives you a local sandbox with a pre-configured inbox — no domain or provider setup.

```bash
pip install nornweave[mcp]
nornweave api --demo
```

API: `http://localhost:8000`. For real email later, see [NornWeave docs](https://github.com/DataCovey/nornweave) (`.env`, Mailgun/Resend, etc.).

### Step 2: Run the agent app

```bash
cd mcp_ai_agents/email_mcp_agent
pip install -r requirements.txt
streamlit run email_mcp_agent.py
```

In the sidebar: set your **OpenAI API key** and **NornWeave API URL** (e.g. `http://localhost:8000`).

### Step 3: Create the support inbox

In demo mode, `GET http://localhost:8000/v1/inboxes` already returns a demo inbox. To create another (or when using a real provider), ask the agent:

```text
Create an inbox named "Support Bot" with username "support". Tell me the inbox id and email address.
```

**Note the inbox id** (e.g. `ibx_...`) — you'll use it in the next steps. In demo you can also list inboxes via the API and use the demo inbox id.

### Step 4: Seed the inbox with test tickets

Ask the agent to send test messages into the inbox (in demo, these show up as threads automatically):

```text
Send three separate emails to support@demo.nornweave.local (or the address from step 3):
1. From alice@example.com, subject "Can't log in", body "I've tried resetting my password twice and it still doesn't work. Help!"
2. From bob@example.com, subject "Billing question", body "I was charged twice this month. Can you check my account?"
3. From carol@example.com, subject "Bug: dashboard is blank", body "After the update, my dashboard shows nothing."
Tell me the thread ids for each.
```

### Step 5: Triage, search, and draft a reply

**Triage** — List recent messages and pick a thread:

```text
In inbox [inbox id], list the most recent messages. Pick the thread about the login issue and show me the conversation.
```

**Search** (optional) — Find threads by topic:

```text
Search inbox [inbox id] for messages about "billing". For each match, give me a one-line summary and the thread id.
```

**Draft and send** — Have the agent draft a reply, then send it:

```text
Draft a short, professional reply for thread [thread id] that acknowledges the problem and says we'll investigate. Don't send yet — just show me the draft.
```

Tweak if needed, then:

```text
Send that draft as a reply in thread [thread id].
```

That's the core loop: **inbox → triage/search → draft → (human approve) → send**.

---

## Advanced

Once you're comfortable with the core loop, try these:

### Attachments

List and inspect attachments in a thread; send replies with attachments:

```text
List the attachments in thread [thread id]. For the first attachment, download it and tell me what it contains.
```

```text
Send a reply in thread [thread id] with the message "Here's the updated config" and attach the file at /path/to/config.yaml.
```

### Escalate what the agent can't handle

Ask the agent to classify threads as "can auto-reply" vs "needs human review":

```text
In inbox [inbox id], list the 10 most recent messages. For each thread, classify as "can auto-reply" or "needs human review" based on complexity. Show me the list with thread ids and classification.
```

### Batch-process multiple threads

Draft replies for all open (customer-last) threads, then send in batch:

```text
In inbox [inbox id], find all threads where the last message is from the customer. For each one, draft a reply. Show me all drafts with thread ids so I can review before sending.
```

```text
Send the drafts for threads [thread id 1], [thread id 2], and [thread id 3].
```

### Wait for a reply (synchronous flow)

Send a follow-up and block until the customer replies (e.g. for scripts or bots):

```text
Send a follow-up in thread [thread id] asking if the customer needs anything else, then wait up to 2 minutes for a reply.
```

Uses the experimental `wait_for_reply` tool.

---

## Other scenarios (same app, different prompts)

The support tutorial covers the full toolkit. Here are other workflows you can build with the same app:

- **Task coordination:** Create an inbox like `tasks@...`, then: "List new messages in inbox [id]. For each message, summarize the request and suggest a one-line task; put them in a single reply to the sender."
- **Stakeholder digest:** "Search inbox [id] for messages about 'weekly report'. Compose one summary email that I can send to leadership."
- **Meeting follow-up:** "After my meeting notes arrive in inbox [id], draft individual follow-up emails to each attendee with their action items."

The same MCP tools power all of these; only the instructions and prompts change.

---

## How it works (under the hood)

```
┌──────────────┐     MCP (stdio)     ┌──────────────────┐     REST API     ┌──────────────┐
│  OpenAI LLM  │◄───────────────────►│  NornWeave MCP   │◄────────────────►│  NornWeave   │
│  (via Agno)  │   tool calls        │  Server          │   HTTP           │  API Server  │
└──────────────┘                     └──────────────────┘                  └──────────────┘
```

1. **NornWeave** — Self-hosted Inbox-as-a-Service: inboxes, threads, Markdown parsing, semantic search.
2. **NornWeave MCP server** (`nornweave mcp`) — Exposes email operations as MCP tools.
3. **This app** — Connects an OpenAI-backed agent (Agno) to those tools so you manage email via natural language.

### MCP tools used in the tutorial

| Tool | What it does | Where |
|------|----------------|--------|
| `create_inbox` | Provision a new email address for the agent | Core (Step 3) |
| `send_email` | Send an email (Markdown → HTML); reply in a thread | Core (Steps 4, 5); Advanced (batch, wait-for-reply) |
| `list_messages` | List messages in an inbox or thread | Core (Step 5); Advanced (escalate, batch) |
| `search_email` | Find messages by keyword | Core (Step 5); Advanced (categorize) |
| `list_attachments` / `get_attachment_content` | List or download attachments | Advanced |
| `send_email_with_attachments` | Send with file attachments | Advanced |
| `wait_for_reply` | Block until a reply arrives (experimental) | Advanced |
