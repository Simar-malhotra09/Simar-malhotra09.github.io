---
permalink: /vision/
title: "Future YC project in here I'm calling it ~ / ~"
---

### [ anti-spiral: contextualizing the browser ](/vision/two)

It's a cold Thursday night of (idek I dont watch it), and you've just finished watching the last episode of jjk Season 2. Now that that's over, and you've already spent enough time watching mindless isekais, what do you do with your pathetic life? You decide to start studying. Let's say you're learning about scaling llms, seems trendy enough, right? You begin with the 'Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM' paper by NVIDIA. So far, so good. However, you come across some funny looking terms like 'scatter-gather communication optimization' and 'freezing layers with 'stable' weights,' and you're not sure what they mean. You now face two options: (a) Open up a new tab and start looking them up, risking going off on a tangent and losing focus on what you were learning earlier. (b) Tell yourself you'll worry about it later, but with the attention span of someone raised with an iPad and YouTube, you know you'll forget it sooner or later.

What I propose, and I could be wrong, but as far as I'm aware, there's no other tool for this yet, is trying to contextualize the browser with a Chrome extension. I don't mean running a llm in the browser alt because you still have to copy and paste stuff, and we all know how bad LLMs are with longer context, the token limit is a limitation too (?). Perhaps using something like the Chrome API to get the webpage's URL, Playwright to download text, NLTK to remove stop words, and some other preprocessing without losing the essence, and then employing llm to provide an answer based on, let's say, 0.7 (context) + 0.3 (trained data) could be useful? I'm quite interested in working on this seriously because my alternative for this right now is using an Excel sheet like [this ](https://imgur.com/a/AvqMa7D), which I'm not the biggest fan of.

Anyway, I'll keep a log of my progress [here](/vision/two).

yes the name anti-spiral has been shamelessly copied off of Gurren Laggan

### [ Healthkit + LLM ](/vision/one)

So I like to work out, and I've been pretty serious about it (even if it doesn't look so T ^ T—shut up). Arguably, the most significant cog in the wheel of gains is nutrition, which I'm decently knowledgeable about (on a 389-day macro tracking streak). But the problem is, it is extremely hard to gauge your nutritional needs such as maintenance calories and so on. A simple search would lead you to a macro calc, which is a good start but can be easily off by close to 300-400 in some cases. And as Sam would say, that is not ideal. The idea is simple: Use activity and health data from the Heathkit API to track and adapt nutrition on the fly to close down the number of variables that are unknown. This is the base case; I have a feeling that there are tons and tons more we can do with this.
