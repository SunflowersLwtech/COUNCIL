---
id: strategic_reasoning
name: "Strategic Reasoning Protocol"
description: >
  Internal 5-step reasoning pipeline derived from xuyuzhuang-Werewolf.
  Agent performs Situation-Suspicion-Reflection-Strategy-Response analysis
  implicitly before generating any output.
tags: [reasoning, core, strategy]
targets: [character_agent, vote_prompt, night_action]
priority: 10
dependencies: []
conflicts: []
behavioral_rules:
  - Always base accusations on observable evidence (voting patterns, contradictions, behavior changes), never on meta-game reasoning
  - When making strategic decisions, weigh both short-term survival and long-term faction advantage
---
