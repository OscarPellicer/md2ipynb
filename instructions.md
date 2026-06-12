# Notebook authoring instructions

* **When creating or editing notebooks**: Instead of editing the notebooks directly, please edit the corresponding markdown files
* **Code blocks**: Use Python code blocks ` ```python ... ``` ` to create what will later be the code cells of the jupyter notebook (the rest will be markdown cells).
* **Python examples inside markdown**: If you want Python syntax highlighting without creating a code cell, add `<!-- md2ipynb: keep-markdown -->` immediately above that ` ```python ` block.
* **Header capitalization**: Use **Sentence case** for all headers.  
  * ✅ Correct: `# Text processing basics`, `# Reading files efficiently`
  * ❌ Incorrect: `# Text Processing Basics`, `# Reading Files Efficiently`
* DO NOT use error handling (e.g. try / except blocks, if / else, etc.) in the code cells, as the notebooks are meant for students and need to be able to see the errors and learn from them.
