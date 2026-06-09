### The ideal goal is to jointly train the tokenizer and transformer with end-to-end accuracy as the objective.This is a challenging problem to solve efficiently, and thus, the tokenizer is generally adapted on a portion of the training dataset and frozen before the transformer is trained.
- jointly train ?
- wtf does adapted mean?

### The maximum sequence length that such models can process is also smaller for the same amount of compute.
### Since tokenizers are usually trained in isolation, they do not directly optimize for extrinsic loss metrics such as the end-to-end perplexity or precision.
- ain't they just said jointly; ah idea, what makes it not efficient?

### Dict size? Avg compressed seq length as a metric to compare tokenizers

### Renyi efficiency, BLEU score, parity, fertility?

###  There are very simple kth-order Markov processes such that in the absence of any tokenization, transformers trained on data drawn this source are empirically observed to predict characters according to a unigram mode
- What is a unigram model?

--- In 10 mins: The goal is to show that the very process of tokenization has some inherent quality that leads to better next-token-prediction, and as long as an impl satisfies that property, it is efficient? ---
