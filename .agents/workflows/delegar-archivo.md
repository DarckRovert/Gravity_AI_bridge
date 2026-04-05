---
description: Delegate the audit of a specific file to the Local Gravity AI
---

This workflow allows Antigravity to automatically send an entire file for the local agent to inspect for vulnerabilities, technical debt, or refactoring, using its memory without consuming cloud quota. Always communicate with the local AI in English for the best results.

// turbo-all
1. **Execute Direct File Audit**
   Inject the file via the pipe injector and ask the local model to perform a thorough review. Replace `<FILE_PATH>` with the actual path.
   ```bash
   cat "<FILE_PATH>" | python ask_deepseek.py "Audit this file for hidden bugs and vulnerabilities. Present a structured report."
   ```

2. **Present Findings**
   Antigravity will read the resulting console output and present it to the user to decide the next steps (e.g. apply fix, discard false positive error).
