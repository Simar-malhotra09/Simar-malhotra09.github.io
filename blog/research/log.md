---
permalink: /blog/research/
title: "Research log"
excerpt: "Research log"
author_profile: false
redirect_from:
---

### 2024/01/24 5:31am

I honestly did not realize research would be this hard. What I'm currently focusing on is sentiment analysis, although I did have a few more interesting ideas in mind. My approach has been naive. I'm looking at datasets that have low best-model accuracy. For example, SST-5 (59.80%) and Yelp fine-grained classification (49.0%). I am trying to replicate and improve those. Although research on NLP/sentiment analysis has been going on for a long time, I wonder what I can really do. What I would like to do is potentially shift the focus from purely academic value to some real-world value. I could work on the IMDb dataset, and for the purpose of proposing a better approach/model, that's cool. But who really cares if I have XYZ accuracy on this dataset of movie reviews? How can sentiment analysis be used in practical applications is what I want to explore a bit. Although that might end up being a pipe dream if I don't focus.

Also, about the datasets, I want to round up the top 10 or so and see what they are lacking. I have an intuition that a lot of these datasets, especially text, tend to be really similar. I admit I don't really know what I'm talking about, though.

## Random

### Datasets:

1. AG News (AG’s News Corpus) is a subdataset of AG's corpus of news articles constructed by assembling titles and description fields of articles from the 4 largest classes (“World”, “Sports”, “Business”, “Sci/Tech”) of AG’s Corpus. The AG News contains 30,000 training and 1,900 test samples per class.

2. Stanford Sentiment Treebank - Fine-Grained
   Stanford Sentiment Treebank with 5 labels: very positive, positive, neutral, negative, very negative.
   Training data is on sentence level, not on phrase level!

3. Yelp-5 (https://github.com/huspark/fine-grained-sentiment-analysis-with-bert)
