The talk describes a meaningfully different problem than the one-line brief did, and it changes what you should build. My earlier plan was built off "hide the metadata so traffic blends into ambient network noise." The partner's actual pitch is about something else.

## What they're actually asking for

Listen to what the presenter kept circling back to. He wants to **mask the plaintext itself** — conceal the real information inside a message "via word replacements and things like that," his Yellow Pages / old-spy-movie codebook analogy (that's a book cipher). The ask is to use generative AI for "dynamic masking and obfuscation of plaintext messages... in such a way that can be easily decoded on the other side," possibly by "training a custom model to speak a specific dialect... Pig Latin and stuff like that." The channels are SMS, Twitter, WhatsApp — consumer social media. The motivating story is the Afghan evacuation, where they reached hundreds of thousands of people over Twitter and WhatsApp and the Taliban was very good at intercepting those comms. The mantra was "talk how they talk and talk where they talk." Audience: one government body to another, e.g. a field operative.

That is **linguistic steganography**, not metadata obfuscation. The goal is to take a sensitive message, turn it into something that reads like ordinary everyday chatter in the right style and platform, send it over an open channel, and have the intended recipient decode it — while an adversary reading all the traffic can't even tell a real communication happened. Encryption hides content but screams "secret here." This is the opposite: look like nothing.

So I'd **drop the LoRa mesh / traffic-analysis plan entirely.** No network simulator, no RF, no signal processing.

## Does this change the track pick?

It strengthens it for your team. The real problem is pure text plus LLMs, which is exactly what AI coding assistants and API orchestration are best at — and API chaining is already in your wheelhouse. There's nothing to simulate and no exotic data to wrangle. Same reasons it was the right call, now even cleaner.

## The revised build (tiered)

Build the simple version first so you always have a working demo, then reach for the impressive one.

**Tier 0 — codebook + LLM cover generation (your safety net).** Sender and receiver share a key. To encode, map the secret message to triggers and prompt an LLM to write a natural, platform-appropriate message — a tweet, a WhatsApp text — that embeds those triggers by a rule (every Nth word, a chosen emoji sequence, synonym selection, an acrostic). To decode, the receiver's parser applies the same key and pulls the hidden content back out. Works with any API model, demos cleanly, and is honestly just chained API calls. Its weakness is low capacity and heuristic security, which you state plainly.

**Tier 1 — generative stego over token distributions (the "wow").** Run a small open model locally (Hugging Face transformers, or llama.cpp with logprobs). At each generation step the model gives a probability distribution over the next token; you use the secret bits to pick among those tokens via arithmetic or Huffman coding. The output is fluent text that's statistically close to normal model output, and the receiver runs the _same_ model and context to invert the coding and recover the bits. This is the state of the art — look up Ziegler et al. 2019 ("Neural Linguistic Steganography"), and the **Meteor** and **Discop** methods. The headline is provable imperceptibility. The risk is synchronization: you need determinism (same model, fixed temperature, identical context) or encode/decode drift apart. Adapt an existing open-source implementation rather than writing the coder from scratch.

## Build the scoreboard regardless

This is what makes the demo land. Assemble a corpus of genuine ordinary messages (real tweets/texts, or LLM-generated chatter as a stand-in), mix in your stego messages, and build an adversary "warden" that tries to flag which ones carry hidden content — start with a perplexity test under a reference model, then a small classifier. Report three numbers: adversary detection AUC (you want ≈ 0.5, a coin flip), capacity (bits per message), and exact-decode rate. The money shot is one chart: detection near chance while decode accuracy sits near 100%.

## Creative angles that map to their own words

- **Persona/platform adaptation** — let the sender pick a cover identity (family WhatsApp group, football Twitter, a regional dialect). This literally is "talk how they talk, talk where they talk," and the dialect/Pig-Latin idea is straight from the pitch.
- **Plausible deniability** — a message that decodes to an innocent meaning under one key and the real meaning under another. Steganography plus deniable encryption; judges love it.
- **Active-warden robustness** — show your scheme survives the adversary lightly paraphrasing or normalizing messages. Harder, optional stretch.

Open your presentation with the Afghan evacuation framing from the talk — it's their own story and shows you listened — then state the threat model crisply: a passive warden who reads every message on an open channel, and you're hiding that a sensitive message exists at all.

## What to learn tonight

1. The prisoners' problem / warden model (Simmons, 1983); passive vs. active warden. This is the vocabulary DIU judges will expect.
2. Steganography vs. cryptography vs. obfuscation — why "blend in" is a different goal than "encrypt."
3. Neural linguistic steganography, conceptually: how secret bits drive token selection via arithmetic/Huffman coding over an LLM's next-token distribution (keywords: Meteor, Discop).
4. Practical plumbing: getting next-token logprobs (HF transformers logits, or an API that returns logprobs) and keeping encode/decode deterministic.
5. Evaluation: a basic text classifier and reading accuracy/AUC.

One caveat worth knowing: the written brief for this track leaned on metadata and synthetic traffic, while the live pitch is clearly about content masking. Build for the content-masking version, since the partner is judging — but you can note timing/posting cadence as a "future metadata layer" in one sentence to cover both readings.

This transcript is the most useful thing you have. It confirms the pivot from my last message and makes the problem dramatically easier than either brief suggested. Quick re-evaluation, then your seven answers.

## Re-evaluation: track confirmed, scope much smaller

No change to the track. This is plaintext content-masking, not metadata — and now it's confirmed from the source. Notre Dame edited the slide: they changed "plain text" to "metadata," but Nick's original prompt was just "can you do masking and unmasking of plain text with generative AI models, as a proof of concept of that workflow." He says outright he kept it to plaintext precisely because it's debuggable in 24 hours.

What's new and important is how much he carved away. He explicitly told you that you do **not** need grammatical correctness, **not** multiple languages, **not** to blend with surrounding traffic (just look benign to "Joe Casual on the street"), **not** to handle pattern-leakage, and that a **cloud model is fine** — don't waste half your day running anything locally. You may assume both parties already share context. "Benign-ness" is allowed to be subjective here. And he is the sole judge, with no rubric, valuing four things he named: feasibility, future improvements, how close you get to the MVP, and honest acknowledgment of challenges.

The MVP in his exact words: type in a string → a model produces a benign-looking message → a second model (or the same one inverted) regenerates the original, or close enough to be usable.

Two strategic reads worth internalizing. First, this plays directly to your strengths — it's API orchestration and prompt design, not ML research. Second, Nick _predicted the failure mode_: "it will get very awkward very quick," meaning the decode comes back lossy or wrong. In this domain, a hallucinated GPS coordinate gets someone killed. **If you engineer around the exact failure he foresaw, you win his respect.** That's the spine of the whole build.

One correction to my earlier message: I floated neural stego (Meteor/Discop, arithmetic coding over token distributions). Drop it as the primary approach — it encodes _bits_, not controllable semantic content like coordinates, and it's fragile. It belongs in your "future improvements" slide as evidence you know the field, not in your build.

**What to learn** shrinks to almost nothing new for you: how to design a reliable encode/decode prompt pair, and the vocabulary to sound credible to Nick (steganography vs. encryption, the "bugged hotel problem" — his own term, hand it back to him; codebook/one-time-pad logic; passive-adversary-reads-plaintext threat model). Your teammates can split UI, slides, and testing.

---

## 1. Stages

- **Stage 0 — Lock scope & story (30–45 min).** Write the one-paragraph threat model and pick your demo scenario (use his Shahed-drone-factory example — it's his). Decide the demo you're driving toward so every build choice serves it.
- **Stage 1 — Core round-trip MVP.** One cloud LLM, an encode prompt and a decode prompt, a hardcoded shared key. Get _any_ message to mask → unmask → recover. This is the whole MVP; everything after is polish and differentiation. (Full step-by-step in Q7.)
- **Stage 2 — The fidelity layer (your differentiator).** Make critical data (coordinates, names, dates, the action) survive the round-trip losslessly, instead of trusting the LLM to "remember" it through a paraphrase. This beats the failure Nick predicted.
- **Stage 3 — Demo UI.** Three panes: sender's real message, the "intercepted channel" view (what the FSB sees), and the receiver's recovered message. Making the adversary's view visible _is_ the pitch.
- **Stage 4 — Lightweight evaluation.** A simple benign-ness check and a decode-accuracy number. Honest, not inflated.
- **Stage 5 — Deck + rehearse.** Frame with his own stories; rehearse the demo with a recorded fallback in case live calls fail.

Rough budget over 28 hours: Stage 0–1 by hour 6, Stage 2 by hour 14, Stage 3 by hour 20, Stage 4 by hour 23, Stage 5 overnight and morning.

## 2. How to actually obtain the model and do each stage

The key mental unlock: **you are not training or hosting anything.** "A model both sides share" does not mean shared _weights_ for the MVP. It means both the sender's encoder and the receiver's decoder call the _same_ cloud model with a _shared key_ (a passphrase/seed/codebook you both hold). The secret isn't the model — it's the key plus the scheme. Nick blessed exactly this: use a cloud model as proof of concept, and _present_ it as though it were a small local model in deployment.

- **Obtain the model:** sign up for one API (Anthropic or OpenAI) and get a key. No fine-tuning, no Ollama, no GPUs for the MVP. Note that the Anthropic API can be called directly from inside a published Claude artifact, so your demo UI and your engine can be one web app with no backend to stand up — a fast path given your team.
- **"The shared algorithm both sides have":** implement it as a shared system prompt plus a shared key string passed into both encoder and decoder. Encoder and decoder are mirror prompts over the same API. In the deck you say: "In deployment this is a small on-device model; for the PoC the shared model is the same API plus a shared key."
- **Encode (mask):** a prompt that takes the clandestine message + the key + a cover theme (e.g., "party planning") and returns a benign message. For reliability, don't ask it to be clever — ask it to apply a _defined_ mapping (see Stage 2).
- **Decode (unmask):** the mirror prompt — benign message + same key → reconstructed original. Run at temperature 0 for determinism.
- **If you want to _show_ a "custom/trained" model** without the cost: use **few-shot in-context examples** as your codebook. A handful of example pairs in the prompt gives you custom, consistent behavior with zero training — functionally a learned codebook, honestly presentable as "we taught the model this scheme via examples; production would fine-tune or distill to a small local model."
- **Optional local-model flex (only if a teammate can babysit it):** `ollama run llama3.2` on a laptop running the same two prompts, shown offline. High impact because it's his stated endgame — but it's optional and he told you not to burn time on it.

## 3. Easiest long-term feature that impresses

Ranked by impact-per-effort:

1. **Bidirectional single model (safest win).** One model/prompt that both masks and unmasks depending on a mode flag, rather than two separate systems. Nick explicitly called this the "fancy" version. It's a trivial change — one system prompt with two modes — and it looks sophisticated. Do this one for sure.
2. **Local-model demo via Ollama (highest impact if you have the time and a spare laptop).** Directly proves his phone-deployment thesis and the "a weird little model is less suspicious than a CIA codebook" argument. Concrete and memorable. Carries setup risk for amateurs, so treat it as a stretch, not a dependency.
3. **Cover-theme / persona selector (flashiest-cheapest).** Let the user pick the cover domain — party planning, sports chatter, family group text. One extra prompt parameter, very visual, and it literally embodies "talk how they talk."
4. **One-language-beyond-English (easy flair).** He said multilingual isn't required, so demonstrating even English → benign-Russian is a free bonus a modern LLM handles in one parameter.

Do #1 and #3 (cheap, safe, visual). Reach for #2 only if Stage 2 finishes early.

## 4. Slide deck structure

Aim for ~11 slides, mapped to what he said he'll judge on.

1. **Title** — project name, team (Juan, Maria, Charlie, Olivia), one-line hook.
2. **The problem / threat model** — the asset-to-handler scenario; adversary reads all plaintext.
3. **Why today's answers fail** — encryption triggers the "bugged hotel problem"; a codebook is a death sentence if seized. Use his terms; cite the Green Revolution and Afghan evacuation.
4. **Our idea** — the LLM as a disposable, innocuous, deniable codebook.
5. **How it works** — architecture diagram: encode → open channel → decode, with the shared key called out.
6. **Live demo** — the three-pane view (sender / intercepted / receiver).
7. **The hard part we solved** — the fidelity layer; show a GPS coordinate surviving the round-trip intact. This is the slide that says "we listened to you."
8. **Does it look benign?** — your evaluation, honest and brief.
9. **Feasibility** — buildable today, cloud now / local later, rough cost.
10. **Limitations & honest challenges** — he specifically rewards this.
11. **Future roadmap + closing vision** — the Great Firewall / Iran citizen-coordination dream (his own long-term goal), then your ask.

## 5. Future improvements to list (time-constrained out of MVP)

Pull these straight from his own words so he hears his wishlist reflected:

- On-device small models running on a phone, no cloud.
- Natural fluency and grammatical correctness across contexts.
- Multilingual support (he mentioned six languages across the planet).
- Pattern/determinism mitigation — same input shouldn't always yield the same cover, to defeat statistical fingerprinting over many messages.
- Objective benign-ness scoring — the NSA-linguist "whole science" he referenced.
- Blending with surrounding/contextual traffic (the metadata layer Notre Dame bolted on).
- Non-text carriers — images/photos, which he floated.
- Robust testing and adversarial red-teaming at scale.
- Per-user unique models and key separation, so a seized model alone can't decode anyone's traffic.
- An open, deployable tool for citizens under censorship.

## 6. Weaknesses to address or acknowledge

- **Lossy / hallucinated decode (the big one).** A wrong recovered coordinate is fatal. _Address in build_ via the Stage 2 keyed structured layer; _acknowledge_ residual risk in the deck.
- **Determinism and pattern leakage.** He excused it for the hackathon — acknowledge it and name the mitigation path.
- **Benign-ness is subjective.** No ground-truth adversary in a day — show your proxy check and say so plainly.
- **Capacity.** A short "birthday cake" message may not carry coordinates + time + name + action. _Address_ by compacting into structured fields or splitting across messages; acknowledge the ceiling.
- **"If the model is seized, can the adversary decode?"** Strong point to make: with a _separate shared key_, possessing the model is not enough to read traffic — unlike a codebook, which is self-incriminating and self-decoding. This turns a weakness into a selling point.
- **Persona plausibility.** Why is this person suddenly sending party texts? Acknowledge; note the persona selector as the fix.
- **Cloud dependence in the MVP** contradicts the local-on-phone thesis. Acknowledge and show you know the local path (even one Ollama screenshot covers this).

## 7. Stage 1, step by step

Goal: a working mask → unmask → recover round-trip on one example. Get this done before anything else so you always have something to show.

1. **Assign and set up (15 min).** Juan drives the API code; one teammate starts the UI shell; one starts slides 2–3; one owns the test log. Create a repo, a Python venv, `pip install anthropic` (or `openai`), and put your API key in an environment variable.
2. **Pick the frozen test case.** Use his example: _"The Shahed drone factory is at 48.4647 N, 35.0462 E. Workday 0800–1700. Plant manager is Viktor Orlov. Destroy it Sunday."_ This is your regression test for the whole hackathon — if a change breaks this round-trip, you revert.
3. **Define the shared key and theme.** Hardcode a key string (e.g., `KEY = "birthday-2026"`) and a cover theme (`"party and gift planning"`). Both encoder and decoder receive these.
4. **Write the encode prompt.** Something like: _"You are a covert message encoder. Shared key: {KEY}. Rewrite the user's secret message as a short, benign {theme} message that a casual reader would find unremarkable. Preserve all specific details (numbers, names, dates, the action) by mapping them into the cover story in a consistent, reversible way, given the key. Output only the benign message."_
5. **Write the decode prompt (mirror).** _"You are a covert message decoder. Shared key: {KEY}. The following is a benign {theme} message that conceals a secret message encoded with this key. Recover the original secret message exactly. Output only the recovered message."_
6. **Run the round-trip** at temperature 0: secret → encode → benign string → decode → recovered string. Print all three.
7. **Measure recovery.** Eyeball first, then score it: did the coordinates, the name, the date, and the action all come back correct? Log pass/fail per field. This field-level accuracy becomes your demo metric.
8. **Iterate the prompts** until the frozen case round-trips cleanly, then try two or three more messages to check it generalizes.

When step 7 shows the coordinates or name coming back wrong — and it will — that's your cue to move to Stage 2: stop trusting the LLM to carry exact data through prose, and instead extract those fields deterministically, let the LLM generate only the natural cover around them, and reinsert on decode by the shared key. Solving that is the thing that wins.

Want me to draft the actual encode/decode prompt pair and a runnable Stage 1 script, or build the three-pane demo as a web app you can present from?
