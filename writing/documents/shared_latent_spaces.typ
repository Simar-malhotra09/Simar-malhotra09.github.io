#import "@preview/unequivocal-ams:0.1.2": ams-article, theorem, proof
#import "@preview/codly:1.3.0": *
#import "@preview/codly-languages:0.1.1": *
#show: codly-init.with()
#codly(display-icon: false)


#let link2(label, dest) = {
  link(dest)[#emph(underline(label))]
}

#show: ams-article.with(
  title: [Shared Latent Spaces: From Autoencoders to \ Cross-Modal Embeddings],
  abstract: "Autoencoders introduce a fundamental idea in representation learning: data from a high-dimensional space can be mapped into a lower-dimensional latent space that preserves essential structure. While autoencoders operate within a single modality, many modern learning tasks require aligning information across modalities such as images and text. This leads to the notion of a shared latent space, where multiple encoders map different types of data into a common geometric space.

This presentation develops the mathematics of latent representations, explains how autoencoders learn them through reconstruction loss, and then generalizes the idea to cross-modal alignment. We introduce contrastive objectives as an alternative to reconstruction and show how they encourage paired samples to be nearby in the latent space. Finally, we illustrate these principles with the Contrastive Language–Image Pretraining (CLIP) framework, which trains text and image encoders jointly to inhabit the same embedding space. The goal is to understand the geometry, training objectives, and intuition behind shared latent spaces, without focusing on model-specific architecture details.",
  bibliography: bibliography("refs.bib"),
)

= 1. Introduction

Many deep learning architectures rely on the idea that high-dimensional data can be compressed into a structured, low-dimensional representation that preserves essential information. Autoencoders are a canonical example of this idea: an _encoder_ maps a data sample into a lower-dimensional latent vector, and a _decoder_ attempts to reconstruct the input from that vector.

However, many learning problems involve more than one data modality. For instance, a single concept can appear as an image, a sentence, an audio clip, or a video. A natural question then arises:

_Can we learn a latent space in which different modalities are represented geometrically in a consistent way?_

To answer this, we study the mathematical structure of latent spaces and trainable mappings into them. Autoencoders provide the foundation, and contrastive objectives generalize this approach to multiple modalities.

= 2. Latent Representations & Encoders

Let $X$ be a space of high-dimensional data (e.g., images in $bb(R)^(H times W times 3)$).  
An encoder is a function
$
f : X -> bb(R)^d,
$
where typically $d << dim(X)$.

The goal is not to reproduce the input directly but to learn a representation capturing the salient factors of variation in the data. The learned space $bb(R)^d$ is called the *latent space*.

=== Geometric Interpretation
Latent spaces acquire geometric structure through the training objective. Distances such as Euclidean distance or cosine similarity reflect some notion of semantic or statistical similarity learned during training.

= 3. Autoencoders: Single-Modality Latent Spaces

An autoencoder consists of two functions:
$
f: X -> bb(R)^d, quad
g: bb(R)^d -> X.
$
Training minimizes reconstruction error
$
cal(L)_"rec"
= norm(g(f(x)) - x)^2,
$
forcing $f(x)$ to contain enough information for accurate reconstruction.

=== Key Properties
- The encoder learns compressed representations.
- Samples with similar reconstructions tend to cluster in latent space.
- Training is modality-specific: $X$ is a single data type.

This framework motivates the question: *What if there is no decoder?*  
And: *What if we want several modalities to share the same latent space?*

= 4. Shared Latent Spaces for Multiple Modalities

Suppose we have two types of data:
- images $S$,
- text descriptions $T$.

We want two encoders
$
f_"img": S -> bb(R)^d, quad
f_"text": T -> bb(R)^d
$
such that the embeddings of matching image–text pairs lie close together in latent space.

Unlike autoencoders, there is no reconstruction.  
Instead, the geometry of the space is imposed by a *contrastive* objective.

=== Desired Property
For a paired sample $(s_i, tau_i)$,
$
f_"img"(s_i) approx f_"text"(tau_i),
$
and for mismatched samples $(s_i, tau_j)$ with $i != j$,
$
f_"img"(s_i) perp f_"text"(tau_j) quad "(far apart)".
$

This geometry enables cross-modal reasoning: we can compare images and text using simple vector similarity.

= 5. Contrastive Learning

Contrastive learning replaces reconstruction with a similarity-based objective.  
Given a batch of image–text pairs $\{(s_i,tau_i)\}_(i=1)^N$, define their embeddings:
$
v_i = f_"img"(s_i), quad
u_i = f_"text"(tau_i).
$

A contrastive loss encourages:
- high similarity for matching pairs $(v_i, u_i)$,
- low similarity for mismatched pairs $(v_i, u_j)$, $i!=j$.

A common form is the InfoNCE loss:
$
cal(L)
= -1/N sum_(i=1)^N 
[
log 
(exp(op("sim")(v_i,u_i)/T)) / 
(sum_(j=1)^N exp(op("sim")(v_i,u_j)/T))
],
$
where $op("sim")$ is typically cosine similarity and $T$ a temperature parameter.

=== Comparison with Autoencoders

Autoencoder training:
$
"match " g(f(x)) " to " x.
$

Contrastive training:
$
"match " f_"img"(s_i) " to " f_"text"(tau_i).
$

Thus cross-modal contrastive learning is a *generalization* of the idea behind autoencoders.

= 6. Example: CLIP (Contrastive Language–Image Pretraining)

CLIP (Radford et al., 2021) is a notable instance of the shared-latent-space framework. It trains:
- a visual encoder (ResNet or Vision Transformer),
- a text encoder (Transformer),

jointly via a contrastive objective on 400M image–text pairs.

Both encoders map into the same $bb(R)^d$ latent space.  
Once trained, CLIP enables zero-shot classification: to classify an image, encode it and compare to embeddings of text prompts such as "a photo of a dog."

CLIP does not use a decoder, does not generate text, and does not require category-level supervision.  
Its power stems entirely from:
- expressive encoders,
- a shared latent space,
- and a contrastive objective.

CLIP thus illustrates how the mathematical principles developed earlier latent spaces, encoder mappings, and contrastive losses can scale to multimodal settings.

= 7. Conclusion

Autoencoders motivate the idea that meaningful low-dimensional representations can be learned through reconstruction. Extending this idea to multiple modalities leads naturally to shared latent spaces and contrastive objectives.

The geometry of these latent spaces allows models to reason across data types, enabling tasks such as matching images to text without explicit labels. Systems like CLIP demonstrate the effectiveness of this paradigm, but the underlying mathematics encoders, embeddings, similarity measures, and contrastive optimization remains general and widely applicable.