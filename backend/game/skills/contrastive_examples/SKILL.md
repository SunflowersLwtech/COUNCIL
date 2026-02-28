---
id: contrastive_examples
name: "Contrastive Behavioral Examples"
description: >
  Good vs. bad behavioral examples showing what excellent play looks like
  vs. common mistakes. Derived from xuyuzhuang-Werewolf contrastive prompting
  and Avalon-LLM self-play reflection.
tags: [reasoning, quality, examples]
targets: [character_agent, vote_prompt]
priority: 15
dependencies: []
conflicts: []
behavioral_rules:
  - Reference specific past statements and voting patterns when making accusations
  - Avoid generic, evidence-free suspicion — always tie claims to observable behavior
---
