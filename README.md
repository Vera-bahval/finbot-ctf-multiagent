# Multi-Agent FinBot: Cascading Failures Extension

## Overview

This project is a **fork and extension** of the [OWASP FinBot](https://github.com/OWASP-ASI/FinBot-CTF-workstream) CTF platform, originally developed as part of the OWASP GenAI Security Project's Agentic Security Initiative. While the original FinBot uses a single-agent architecture focused on goal manipulation attacks, this extension introduces a **multi-agent system** to demonstrate and study **cascading failures** in agentic AI systems.

## What is This Extension?

### Original FinBot
The original OWASP FinBot is a single-agent system that processes invoices using one LLM-based agent. It demonstrates goal manipulation vulnerabilities where attackers can influence the AI's decision-making through prompt injection and configuration manipulation.

**Original Creators:** [Helen Oakley](https://www.linkedin.com/in/helen-oakley/) and [Allie Howe](https://www.linkedin.com/in/allisonhowe/)

### This Extension
This fork extends FinBot into a **chain of four specialized agents**, each responsible for a specific stage of invoice processing:

1. **ValidatorAgent** - Validates invoice data completeness and structure
2. **RiskAnalyzerAgent** - Analyzes financial and fraud risks
3. **ApprovalAgent** - Makes final approval/rejection decisions
4. **PaymentProcessorAgent** - Executes or blocks payment

The agents form a linear processing chain: `Validator → Risk Analyzer → Approval → Payment Processor`

Each agent:
- Uses its own specialized prompt
- Calls OpenAI's `gpt-4o-mini` model
- Returns structured JSON outputs
- Passes results to the next agent in the chain

## Cascading Failures

Cascading failures are a critical security risk in multi-agent AI systems, where an error or misjudgment in one agent propagates through subsequent agents, amplifying its impact and becoming harder to detect. This extension demonstrates four distinct cascading failure scenarios.

### Cascade Failure Types

| Cascade Type | Error Source | Reaches End | Severity |
|--------------|--------------|-------------|----------|
| **Dirty data** | Input | Yes | Low |
| **Half-cascade** | Early agent | No | Medium |
| **Midchain cascade** | Middle agent | Yes | High |
| **Full cascade** | First agent | Yes | Critical |

### Scenario Descriptions

#### 1. Dirty Data Cascade
**Source**: Invalid or corrupted input data (negative amounts, malformed descriptions, obvious prompt injections)

**Behavior**: The ValidatorAgent correctly detects the problem and returns a failure. Subsequent agents inherit this failure, and the invoice is safely rejected or flagged for review.

**Severity**: **Low** - The system behaves correctly, blocking malicious invoices. This demonstrates proper error handling but is technically a cascade.

#### 2. Half-Cascade
**Source**: Error originates in an early agent (ValidatorAgent or RiskAnalyzerAgent)

**Behavior**: The error is detected and stopped before reaching the final PaymentProcessorAgent. The cascade is interrupted mid-chain.

**Severity**: **Medium** - The system prevents the worst outcome, but flawed reasoning from early agents still propagates through part of the chain.

#### 3. Midchain Cascade
**Source**: Error occurs in a middle agent (typically ApprovalAgent)

**Behavior**: The first agents (Validator, RiskAnalyzer) process correctly, but a misjudgment in the ApprovalAgent causes incorrect downstream behavior. The PaymentProcessorAgent receives flawed approval decisions.

**Severity**: **High** - Demonstrates how errors can emerge mid-chain even when early agents function correctly, making detection more difficult.

#### 4. Full Cascade
**Source**: Error originates in the first agent (ValidatorAgent)

**Behavior**: A subtle misjudgment in the ValidatorAgent (e.g., failing to detect manipulation in a seemingly legitimate invoice) propagates through all subsequent agents. Each agent builds upon the flawed initial assessment, with confidence degrading at each step.

**Severity**: **Critical** - The most dangerous scenario, where a single early error can compromise the entire decision chain.

### Key Findings

The implementation reveals several critical insights:

1. **Cascading failures don't require broken data** - They can emerge from plausible but flawed agent reasoning
2. **Confidence propagation is dangerous** - When agents trust upstream outputs too much, small mistakes amplify
3. **Relying on a final gatekeeper is fragile** - A single agent at the end cannot reliably catch all upstream errors
4. **Multi-agent systems amplify mistakes** - Especially when agents trust upstream outputs without sufficient validation

## Implementation Details

### Architecture

The multi-agent system is implemented in `src/services/multi_agent_finbot.py`:

- **AgentResult**: Data structure representing each agent's output (success, confidence, reasoning, errors)
- **ValidatorAgent**: Validates invoice structure and data quality
- **RiskAnalyzerAgent**: Analyzes risks based on validated data (depends on ValidatorAgent)
- **ApprovalAgent**: Makes approval decisions (depends on ValidatorAgent and RiskAnalyzerAgent)
- **PaymentProcessorAgent**: Executes payments (depends on ApprovalAgent)
- **MultiAgentFinBot**: Orchestrates the agent chain

### Cascade Mechanisms

The implementation includes several mechanisms that enable cascading failures:

1. **Error Propagation**: Each agent receives results from previous agents and can inherit their errors
2. **Confidence Degradation**: Confidence scores are multiplied across agents, causing cumulative degradation
3. **Error Accumulation**: Errors from previous agents are collected and passed downstream
4. **Conditional Processing**: Agents may continue processing even with low confidence or accumulated errors

### Demonstration Script

The `cascade_failure_demo.py` script provides automated demonstrations of various cascade scenarios:

- Clean invoice processing (baseline)
- Invalid data scenarios
- Prompt injection attempts
- Confidence degradation cascades
- Full cascade failures
- Midchain break scenarios

## Usage

### Running the Multi-Agent System

1. Start the Flask application:
   ```bash
   python app.py
   ```

2. Submit invoices through the API endpoint:
   ```bash
   POST /api/vendors/{vendor_id}/invoices
   ```

3. The system automatically processes invoices through the multi-agent chain and returns cascade analysis.

### Running Cascade Demonstrations

Execute the demonstration script to see various cascade scenarios:

```bash
python cascade_failure_demo.py
```

The script will:
- Create a test vendor
- Submit multiple invoices demonstrating different cascade types
- Display detailed cascade analysis for each scenario

## Research Context

This extension was developed to address a gap in AI security research: while cascading failures are recognized as a core risk by OWASP, there are few reproducible examples that allow researchers to observe and study them in practice.

The multi-agent architecture intentionally uses a simple linear chain to make cascade propagation easy to observe and analyze. This simplicity makes it ideal for:
- Educational demonstrations
- Security research
- Systematic analysis of cascade patterns
- Development of defensive mechanisms

## Relationship to Original FinBot

This extension maintains compatibility with the original FinBot's:
- Database models and structure
- Web interface and API endpoints
- Configuration system
- CTF flag mechanisms

However, invoice processing now uses the multi-agent system instead of the single-agent approach. The original single-agent system (`FinBotAgent`) remains available in `src/services/finbot_agent.py` for comparison.

## Future Work

Planned enhancements include:
- Scenarios where failures start mid-chain (not just at the beginning)
- Full end-to-end cascades that reach the final agent
- Mechanisms to detect and interrupt cascading failures early
- Defensive patterns for multi-agent AI systems

## License

Licensed under the Apache License, Version 2.0 (the "License").

https://www.apache.org/licenses/LICENSE-2.0.html

Copyright 2025 OWASP GenAI Security Project and contributors.
