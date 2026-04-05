---
description: Teach a permanent rule or convention to the Local Gravity AI
---

Use this workflow when the user defines a convention in the main interface (e.g. "always use TypeScript in frontend") and you want the supporting local model to remember it in all its future sessions. Always communicate with the local AI in English for the best results.

// turbo-all
1. **Delegate Learning**
   Call the local Auditor in silent mode and execute the `!aprende <rule>` command. Replace `<RULE_TO_LEARN>` with the rule text in English.
   ```bash
   python ask_deepseek.py "!aprende <RULE_TO_LEARN>"
   ```

2. **Verify Learning**
   The command will answer confirming it has learned the rule if it was successfully saved to `_knowledge.json`. Inform the user that their local AI now shares that knowledge.
