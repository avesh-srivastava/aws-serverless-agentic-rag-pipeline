# Orchestration Agent

## Overview
The Orchestration Agent coordinates all other agents and manages the complete RAG pipeline workflow.

## Lambda Functions
- **trigger_step_function.py** - API Gateway entry point

## Step Functions
- **StateMachineRetrieval.json** - Complete pipeline orchestration

## Capabilities
- Multi-agent coordination
- Error handling and recovery
- Pipeline monitoring and logging
- Session and query ID management