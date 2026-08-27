# Provider Latency and Cost Reference

**Reviewed:** August 28, 2026
**Scope:** Synthetic, redacted AI-scribe requests only

| Adapter | Default model | Published throughput / measured latency | API price | Operational note |
|---|---|---|---|---|
| Groq | `openai/gpt-oss-20b` | Groq publishes approximately 1,000 generated tokens/second; application end-to-end latency is captured per completed job and exposed by `GET /provider-usage`. | USD 0.075 per 1M input tokens and USD 0.30 per 1M output tokens. | Hosted; requires an ignored API key and verified redaction before invocation. |
| Ollama | `qwen3:4b` (configurable) | Hardware-specific. Measure locally through the same usage endpoint; no unverified latency value is claimed. | No per-token local API charge; hardware, electricity, and operations are not free. | Local OpenAI-compatible `/v1/chat/completions`; bind it to loopback/private networks only. |

Groq model, price, throughput, context, and strict structured-output support are
documented by [Groq's GPT-OSS 20B model page](https://console.groq.com/docs/model/openai/gpt-oss-20b)
and [Groq Structured Outputs](https://console.groq.com/docs/structured-outputs).
Ollama documents its local OpenAI-compatible endpoint and supported request
fields in [OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility),
and its local authentication behavior in
[Ollama authentication](https://docs.ollama.com/api/authentication).

## Runtime evidence

The worker persists provider/model identifiers, token counts, timestamps, and
estimated cost—not prompts or clinical text. `GET /provider-usage` aggregates:

- call count;
- input and output tokens;
- average claim-to-completion latency;
- estimated USD cost.

Until a genuine synthetic call is run with a newly rotated key or a local
Ollama model, the dashboard correctly returns no live measurement rather than
presenting mocked latency as provider evidence.
