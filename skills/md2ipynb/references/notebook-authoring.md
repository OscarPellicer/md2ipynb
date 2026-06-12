# Notebook authoring rules

Use these rules when creating or substantially rewriting instructional notebooks.

- Prefer editing the Markdown intermediate instead of raw `.ipynb` JSON.
- Use ` ```python ` fenced blocks only for content that should become notebook code cells.
- Use plain fenced blocks for code examples that should remain in Markdown cells.
- To keep Python syntax highlighting without creating a code cell, put `<!-- md2ipynb: keep-markdown -->` immediately above the ` ```python ` block.
- Use sentence case for all headers.
  - Correct: `# Text processing basics`, `# Reading files efficiently`
  - Incorrect: `# Text Processing Basics`, `# Reading Files Efficiently`
- Do not use student-facing error handling such as `try`/`except` or `if`/`else` in code cells. These notebooks are meant for students, and learners should be able to see real errors and learn from them.
