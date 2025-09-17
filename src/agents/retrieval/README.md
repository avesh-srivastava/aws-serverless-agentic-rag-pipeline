# Knowledge Retrieval Agent

## Overview
The Knowledge Retrieval Agent performs sophisticated search and ranking to find the most relevant information for user queries.

## Lambda Functions
- **aai_hybrid_search_fusion.py** - BM25 + kNN search with RRF fusion
- **aai_cross_encoder_rerank.py** - SageMaker-based reranking
- **aai_mmr_diversity.py** - Maximal Marginal Relevance filtering
- **aai_final_results.py** - Quality metrics and result preparation

## Capabilities
- Hybrid search combining lexical and semantic approaches
- Cross-encoder reranking for improved relevance
- MMR diversity filtering to reduce redundancy
- Quality metrics calculation and monitoring