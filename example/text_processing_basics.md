# text_processing_basics.ipynb

## Text processing basics

This notebook introduces a simple text processing workflow using a short collection of sentences.

## Import the tools

```python
from collections import Counter
import re
```

## Create a small corpus

We start with a few short text snippets so the transformations are easy to inspect.

```python
documents = [
    "Natural language processing helps computers work with text.",
    "Text processing often starts with normalization and tokenization.",
    "Simple examples make notebook workflows easier to understand.",
]

documents
```

## Normalize the text

Here is a plain fenced example that should remain inside the markdown cell on round-trip:

```
normalized = text.lower().strip()
```

Now we perform the actual normalization in a code cell.

```python
normalized_documents = [document.lower() for document in documents]

normalized_documents
```

## Tokenize the text

```python
tokenized_documents = [re.findall(r"[a-z]+", document) for document in normalized_documents]

tokenized_documents
```

## Count token frequencies

```python
all_tokens = [token for document in tokenized_documents for token in document]
token_frequencies = Counter(all_tokens)

token_frequencies.most_common(10)
```

## Inspect a few common words

```python
selected_words = ["text", "processing", "notebook", "workflows"]
{word: token_frequencies[word] for word in selected_words}
```

## Next steps

Possible follow-up edits for an agent include adding stopword filtering, building a vocabulary table, and turning the notebook into a longer teaching sequence.
