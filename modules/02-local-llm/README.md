# 02 · Local LLM with Ollama

**Goal:** run a model locally and call it from code.

## Ideas
Ollama serves models over HTTP (`/api/tags`, `/api/generate`, `/api/chat`). Small models are fast and weak; you will measure that tradeoff in Module 08.

## Lab
1. Start Ollama, then `ollama pull llama3.2:1b`.
2. `curl localhost:11434/api/tags`
3. `curl localhost:11434/api/generate -d '{"model":"llama3.2:1b","prompt":"Say hi","stream":false}'`
4. Time it. Try `"options":{"num_predict":16}` and compare.
5. Read `app/gateway/main.py` to see how the gateway makes the same call.

## Checkpoint
`make verify-02`

## Stretch
Pull a second model and compare latency and answer quality on three prompts.
