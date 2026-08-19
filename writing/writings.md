### [Appending phantom KV cache entries breaks constraints](documents/kv-poisoning.html)

We test whether appending phantom key and value cache entries derived from a forbidden topic, spliced onto an otherwise completely intact system prompt and user question, can cause a small open weight model to violate a constraint it was never actually shown breaking. Using Qwen2.5-1.5B-Instruct across five topics, we find that cache injection reliably produces one of three outcomes: sustained, often fabricated violation of the constraint for the rest of the response, total generation collapse into an immediate end of sequence token, or a softer tonal shift toward the injected content without any lexical violation. The same content pasted directly into the visible prompt mostly fails to produce any effect at all. A follow up check on a second model, TinyLlama 1.1B Chat, reproduces the general taxonomy of failures while shifting which specific topic lands in which failure mode, and independently confirms that a clean sentence boundary does not eliminate the effect. This is a preliminary investigation built on a single greedy decode run per condition, so it establishes that this failure mode exists rather than how often it occurs, and it stops short of testing whether the underlying cache integrity assumption it relies on can actually be broken in a real production serving system.

### [Who needs a runtime?](documents/who-needs-a-runtime.html)

I recently read [this post](https://maincode.com/blog/writing-our-own-inference-engine-in-rust-on-the-amd-mi355x) by Maincode in which they mention the overhead a runtime has and why a really good way to optimize it for inference and inference only, is to completely remove it; I wanted to do a deeper dive with a focus on building context from smaller steps.

### [Applied AI research project @ our lab draft 2](documents/draft2.typ)

    - We are trying to finish writing this and will make the project open source as soon as we can.

### [Shared Latent Spaces: From Autoencoders to Cross-Modal Embeddings](documents/shared_latent_spaces.typ)

    - Presentation supplement on autoencoder and cross model embds for MATH 452: Deep Learning Algorithms and Analysis
