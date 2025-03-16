# Diane Project Context

[Paste your original project summary/architecture from this thread here]

## Current State (Update this weekly!)

- **Completed**: Postgres DB setup (WIP), Whisper integration
- **Next Focus**: Chroma DB integration, Hybrid Search

## Workflow Diagram

```mermaid
graph TD
  A[Audio Recording] --> B(Whisper Transcription)
  B --> C[(Postgres: Dates/Metadata)]
  B --> D[(Chroma: Text Embeddings)]
  C & D --> E(LangChain Hybrid Search)
  E --> F[Query Response]
```
