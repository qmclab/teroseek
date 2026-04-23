# TeroSeek
An intelligent dialogue platform exclusively dedicated to terpenoids research

TeroSeek is a terpenoid-oriented knowledge retrieval and expert Q&A system. It integrates a domain knowledge base (`TeroSeek-KB`), a KG-RAG reasoning pipeline, and an MCP service interface to provide accurate and evidence-backed answers for both researchers and AI agents. The core goal of this system is to transform fragmented, cross-disciplinary terpenoid literature into a structured and computable knowledge network, enabling users to discover relationships among molecular structures, biological sources, mechanisms, and applications more efficiently.

The current release is built from large-scale literature mining and structured extraction. Starting from 259,687 candidate records, TeroSeek curated a final corpus of 126,647 terpenoid-related publications and currently includes over 60,000 full-text documents. The pipeline has generated 3,322,223 knowledge triplets and cataloged 130,486 terpenoid molecule names, with biological source information explicitly mentioned in 110,431 records. This data scale provides broad coverage and supports robust evidence retrieval for terpenoid research scenarios.
## MCP-Server
## Supplementary Files Overview

This section describes the key files and directories included in this supplementary package.

### 1) File: `response accuracy.xlsx`

This Excel file contains raw data for evaluating model hallucinations in terpenoid structural classification, with four sheets:

- `Easy`: 120 molecules with high data availability (>50 related publications).
- `Middle`: 120 molecules with moderate data availability (5-10 related publications).
- `Hard`: 120 molecules with limited data availability (2-3 related publications).
- `Prompt`: System prompts used to query the evaluated LLMs.

For `Easy`, `Middle`, and `Hard`, rows with full model consensus are sorted to the bottom, while divergent or incorrect outputs are prioritized at the top. Each model output has a dedicated column, and verbatim unprocessed responses are retained in columns suffixed with `_raw`.

### 2) Directory: `reference accuracy`

This directory stores full results for reference verification tests:

- Top-level subdirectories are organized by model name.
- Each model directory contains 20 pairs of files for tested molecules:
  - `.txt`: full initial model response.
  - `.xlsx`: extracted cited references for verification.
- In verification spreadsheets, each reference is labeled manually with:
  - `fake` (hallucinated),
  - `off_topic` (irrelevant),
  - `good` (accurate).

A value of `1` is entered in the corresponding column for each reference.

### 3) Directory: `Good Response`

This directory contains representative high-quality responses from the system. Query index details are provided in Table S1. Filenames correspond to the original question text, and each file includes the full Expert Q&A Agent output (system metadata, token usage, additional information, formal answer, and references).

### 4) Directory: `Ambiguous Response`

This directory contains responses that were successfully generated but may include retrieval inaccuracies requiring human verification. Query titles are indexed in Table S2. Each file records the complete Expert Q&A Agent output, including metadata, token usage, additional context, formal answer, and bibliography.

### 5) Directory: `Bio Source Benchmark`

This directory contains the five benchmark questions used in the main text:

- `all_llm_response.xlsx`: full responses from all evaluated models.
- Five `.docx` files: detailed and fully cited TeroSeek responses for each benchmark query.

### 6) File: `Expert Research Demo.docx`

This document presents an Expert Research Agent case study on **"Carvacrol as a Bacterial Growth Inhibitor"**, with a synthesized review supported by 200 cited references.

## MCP-Server

## Core Configuration

The TeroSeek MCP retrieval assistant operates on an SSE (Server-Sent Events) architecture. Please add the following JSON content to your MCP client configuration file (e.g., `claude_desktop_config.json` for Claude Desktop, or the equivalent configuration for other compatible clients):

```json
{
  "mcpServers": {
    "terpene-local-service": {
      "isActive": true,
      "name": "TeroSeek-KB",
      "type": "sse",
      "description": "TeroSeek Knowledge Graph for Terpenoids Research",
      "url": "https://teroseek.qmclab.com/mcp/sse",
      "baseUrl": "https://teroseek.qmclab.com/mcp/sse",
      "provider": "",
      "providerUrl": "",
      "logoUrl": "",
      "tags": [],
      "installSource": "unknown",
      "isTrusted": true,
      "timeout": "20",
      "longRunning": true
    }
  }
}
```

## Deployment Guide

### Common Parameters

Use the following values in all clients:

| Field | Value |
| --- | --- |
| Name | `TeroSeek-KB` |
| Type | `SSE` |
| URL | `https://teroseek.qmclab.com/mcp/sse` |
| isActive | `true` |

---

### Option A: Claude Desktop

1. Open the Claude Desktop configuration file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
2. Merge the `terpene-local-service` block into `mcpServers`.
3. Save the file and fully restart Claude Desktop.
4. Verify that the `TeroSeek-KB` tool appears and is available in chat.

---

### Option B: Cursor / Other IDEs

1. Open IDE settings and go to **Features > MCP**.
2. Click **Add New MCP Server**.
3. Fill in the following values:
   - Type: `SSE`
   - Name: `TeroSeek-KB`
   - URL: `https://teroseek.qmclab.com/mcp/sse`
4. Save and confirm the service status is **Active** (`isActive: true`).

---

### Option C: Cherry Studio

1. Open **Settings** (gear icon).
2. Go to the **MCP (Model Context Protocol)** tab.
3. Click **Add** / `+` / **Add MCP Server**.
4. Configure:
   - Name: `TeroSeek-KB`
   - Type: `SSE (Server-Sent Events)`
   - URL: `https://teroseek.qmclab.com/mcp/sse`
5. Save and enable the server.
6. Verify that TeroSeek tools are available in chat.


