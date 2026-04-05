---
description: Delegate an intensive technical task to the Local Senior Auditor
---

This workflow is how **Antigravity** leverages the Gravity Server to perform heavy Coder work (e.g. writing entire modules) using the human's local GPU backend. Always communicate with the local AI in English for the best results.

// turbo-all
1. **Verify the Ecosystem**
   Evaluate which engine Gravity is running on and its available memory.
   ```bash
   python ask_deepseek.py "!info"
   ```

2. **Delegate via Direct Pipe (E.g. File Audit)**
   If you need the local AI to review a complete code block (or a long error), assume the temporary Coder profile and send it via pipe:
   ```bash
   cat THE_FILE_WITH_PROBLEMS.py | python ask_deepseek.py "Write the complete fix for the errors in this file. Provide the corrected code without excuses and avoid excessive markdown."
   ```

3. **Incorporate the Solution**
   Read the console output, correct or adapt it if you notice any deficiency from the local model, and implement it for the user.
