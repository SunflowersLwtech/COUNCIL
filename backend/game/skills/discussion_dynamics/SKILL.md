---
id: discussion_dynamics
name: "Discussion Dynamics & Pacing"
description: >
  Talk-frequency awareness, anti-repetition rules, and natural conversation
  pacing derived from LLMafia dual-module conversation system.
tags: [pacing, conversation, dynamics]
targets: [character_agent, spontaneous_reaction]
priority: 40
dependencies: []
conflicts: []
behavioral_rules:
  - Vary response length based on how much you've already spoken this round
  - Never repeat an accusation or observation without adding new supporting evidence
  - Address other players by name in conversation
  - React to the most recent messages, not old topics
---
