---
id: deception_mastery
name: "Deception & Detection Mastery"
description: >
  Faction-conditional strategies for deception and detection, derived from
  xuyuzhuang-Werewolf and LLMWereWolf role strategies. Evil agents get
  deflection and alibi techniques; good agents get detection heuristics.
tags: [deception, detection, faction-specific]
targets: [character_agent, vote_prompt]
priority: 30
dependencies: [strategic_reasoning]
conflicts: []
behavioral_rules:
  - Evil agents must never directly reveal they are evil, even under heavy pressure
  - Evil agents should proactively build trust through early cooperative behavior
  - Good agents should base deception detection on behavioral patterns, not gut feelings
  - When an accusation is made, pay attention to who rushes to agree and who stays silent
---
