---
id: memory_consolidation
name: "Memory Consolidation System"
description: >
  3-tier memory tracking (STM/Episodic/Semantic) derived from ai-traitors-v2
  and ai-town generative agent reflection. Helps agents maintain beliefs
  about each player and synthesize round memories into strategic conclusions.
tags: [memory, tracking, beliefs]
targets: [character_agent, round_summary]
priority: 20
dependencies: []
conflicts: []
behavioral_rules:
  - Track trust levels for each player based on accumulated evidence, not first impressions
  - Update beliefs when new evidence contradicts old assumptions
  - Pay special attention to behavioral changes between rounds
---
