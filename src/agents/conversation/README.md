# Conversation Agent

## Overview
The Conversation Agent manages multi-turn conversations, maintains context, and generates intelligent responses.

## Lambda Functions
- **aai_read_history.py** - Retrieves conversation history
- **aai_query_embedding.py** - Generates query embeddings
- **aai_synthesize_answer.py** - Creates LLM responses
- **aai_store_conversation.py** - Persists conversation data

## Capabilities
- Multi-turn conversation management
- Context-aware response generation
- Conversation history persistence
- Intent detection for escalation