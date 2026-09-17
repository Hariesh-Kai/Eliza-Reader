# Eliza Reader

## System Boundaries & Risks

### 1. System Boundary

Eliza Reader is a personal-use application designed to take a novel webpage provided by the user, identify the actual story content, understand its narrative structure, and convert that content into natural spoken narration.

The system boundary begins when the user provides a website URL and ends when Eliza Reader produces spoken narration for the identified story content.

### 2. What Is Inside the System

The following capabilities are part of Eliza Reader:

**Website Input**

* Accept a novel/chapter webpage URL from the user.
* Access and process the webpage.
* Handle the webpage's visible and relevant content.

**Webpage Content Analysis**

* Scan the webpage contents.
* Distinguish story content from surrounding webpage elements.
* Identify and ignore non-story content such as headers, navigation, advertisements, footers, comments, buttons, and unrelated links.
* Identify the chapter title and story boundaries when possible.

**Story Processing**

* Extract the clean novel text.
* Detect narration and dialogue.
* Identify characters appearing in the chapter.
* Determine the likely speaker of dialogue.
* Maintain character identity across chapters where possible.

**Narration Planning**

* Assign voices to characters.
* Allow voice characteristics to be independent of the character's biological gender.
* Determine appropriate speaking speed.
* Determine pauses and emphasis.
* Determine emotional or contextual delivery where possible.

**Audio Generation**

* Convert the planned narration into speech.
* Switch between narrator and character voices.
* Maintain consistent character voices.
* Play the generated narration to the user.

**Real-Time Processing**

* Process upcoming story content while current content is being read.
* Avoid requiring the entire novel to be converted into audio before playback can begin.

---

### 3. What Is Outside the System

The following are not part of the initial system:

**Publishing or Distribution**

* Eliza Reader is not intended to publish or distribute the novel.
* It is not intended to provide the novel or generated audiobook to other users.

**Novel Hosting**

* Eliza Reader does not host the novel website.
* The application relies on the webpage supplied by the user.

**General Web Browser**

* Eliza Reader is not intended to become a complete web browser.
* Its purpose is to obtain and process novel content rather than provide general internet browsing.

**Perfect Literary Understanding**

* Eliza Reader does not need to understand every aspect of the novel exactly as a human reader would.
* Character relationships, emotions, sarcasm, implied meaning, and ambiguous dialogue may sometimes be interpreted incorrectly.

**Perfect Human-Level Narration**

* The system may produce natural narration, but it cannot guarantee that every sentence will be performed exactly as a professional human audiobook narrator would perform it.

---

# 4. Technical Boundaries

### Website Boundary

The application can only process content that it can successfully access.

A website may:

* Require JavaScript.
* Dynamically load chapter content.
* Change its HTML structure.
* Require authentication.
* Block automated access.
* Use anti-bot mechanisms.
* Present content in an unusual format.

Therefore:

> If Eliza Reader cannot access the actual story content, the narration pipeline cannot begin.

The system should report this clearly instead of silently producing incorrect text.

### Content Extraction Boundary

The system must make a distinction between:

**"I found text on the webpage"**

and

**"I found the novel."**

Finding text is not sufficient.

The extraction system should have confidence in the identified story region before sending it to the narration system.

If confidence is low, Eliza Reader should be able to ask the user to confirm or select the story region rather than reading unrelated webpage content.

### AI Understanding Boundary

The AI analysis layer is probabilistic.

It may incorrectly determine:

* Who is speaking.
* Which character a pronoun refers to.
* The emotion of a sentence.
* Whether a sentence is narration or dialogue.
* The intended tone of a conversation.
* The relationship between characters.

The system should therefore treat AI interpretation as a plan rather than unquestionable truth.

### Audio Boundary

The quality of the final narration depends on the selected TTS/voice technology.

Eliza Reader controls the narration plan, but the underlying voice engine determines much of the final audio quality.

---

# 5. Major Risks

## Risk 1 — Incorrect Story Extraction

This is one of the most important risks.

The application could accidentally read:

* Website navigation
* Advertisements
* Comments
* Recommended novels
* Footer text
* Copyright notices
* Buttons
* Chapter navigation

instead of the novel.

**Impact:** High

**Mitigation:**
Use multiple signals to identify the story region rather than relying on a single HTML selector. Include a confidence score and eventually provide manual correction.

---

## Risk 2 — Website Changes

The website may change its HTML structure without warning.

A scraper that works today may stop working tomorrow.

**Impact:** Medium/High

**Mitigation:**
Build content extraction around general webpage characteristics instead of website-specific CSS selectors wherever possible. Keep the extraction layer separate from the rest of the application.

---

## Risk 3 — Website Access Failure

The website may block automated requests or require JavaScript/authentication.

**Impact:** High

**Mitigation:**
Initially support straightforward accessible pages. Later, consider browser-based page rendering where appropriate. Never assume that a normal HTTP request is sufficient.

---

## Risk 4 — Incorrect Character Identification

The system may miss a character, create duplicate character identities, or confuse two characters with similar names.

**Impact:** Medium

**Mitigation:**
Maintain a persistent character registry and use context from previous sections/chapters when resolving characters.

---

## Risk 5 — Incorrect Speaker Identification

The system may assign dialogue to the wrong character.

For example:

```text
"You're coming with me."

He looked at her.

"Of course."
```

The second line may be ambiguous without understanding the surrounding context.

**Impact:** High

**Mitigation:**
Use surrounding narration and conversation context rather than analyzing each sentence independently. Maintain conversation state.

---

## Risk 6 — Inconsistent Character Voices

A character could accidentally receive different voices during different chapters.

**Impact:** Medium

**Mitigation:**
Create a persistent voice registry:

```text
Character → Voice ID
```

Once assigned, the voice remains associated with that character unless deliberately changed.

---

## Risk 7 — Incorrect Emotion or Delivery

The system may interpret sarcasm as sincerity, anger as calmness, or excitement as ordinary narration.

**Impact:** Medium

**Mitigation:**
Treat emotion as a narration suggestion rather than absolute truth. Use surrounding context and conservative defaults when confidence is low.

---

## Risk 8 — Real-Time Processing Delays

If story analysis and audio generation are slower than playback, the reader could reach the end of the prepared audio and have to wait.

**Impact:** High

**Mitigation:**
Use a pipeline with look-ahead processing:

```text
Currently speaking
       │
       ├── Next section → analyzing
       │
       ├── Following section → preparing
       │
       └── Future section → waiting
```

Audio should be buffered ahead of playback.

---

## Risk 9 — TTS Errors

The voice engine may:

* Mispronounce names.
* Misread punctuation.
* Handle unusual formatting badly.
* Produce unnatural pauses.
* Fail to convey certain emotions.

**Impact:** Medium

**Mitigation:**
Preprocess text before sending it to TTS and maintain a pronunciation/customization layer for recurring names and unusual words.

---

## Risk 10 — Excessive AI Cost or Resource Usage

If every sentence requires a large AI model, processing an entire novel could become expensive or slow.

**Impact:** Medium

**Mitigation:**
Use traditional programming and lightweight NLP wherever possible. Reserve expensive AI reasoning for tasks that genuinely require contextual understanding.

---

## Risk 11 — Incorrect Audio Due to AI Hallucination

The AI should never rewrite or invent parts of the novel while preparing narration.

For example, the system must not turn:

```text
Original:
He entered the room.
```

into:

```text
Narration:
He slowly entered the dark and mysterious room.
```

unless such transformation is explicitly intended by a future feature.

**Impact:** High

**Mitigation:**
Separate:

**SOURCE TEXT**

from

**NARRATION INSTRUCTIONS**

The AI should determine how the source text is spoken, not silently change the story.

---

## Risk 12 — Privacy and Data Handling

The application may process webpage content and potentially send text to external AI/TTS services.

**Impact:** Medium

**Mitigation:**
Clearly separate local processing from external services. Avoid storing unnecessary novel text or generated audio. If external APIs are used, understand what data is transmitted and how the provider handles it.

---

# 6. Important Design Principle

Eliza Reader should follow one fundamental rule:

> **The story text is authoritative. AI decides how to read it, not what story to invent.**

The system can decide:

```text
Who is speaking?
Which voice?
What emotion?
What speed?
Where should there be a pause?
```

But it should preserve:

```text
What the author actually wrote.
```

This distinction is important because Eliza Reader is a **narration system**, not a story-generation system.

---

# 7. Failure Philosophy

When Eliza Reader is uncertain, it should prefer:

**"I am not sure."**

over:

**"I will guess and read something incorrect."**

For example:

```text
Story extraction confidence: 98%
→ Continue automatically.

Story extraction confidence: 62%
→ Ask user to confirm story region.

Speaker confidence: 95%
→ Use identified character.

Speaker confidence: 48%
→ Use a safe/default narration strategy.
```

This makes the system more reliable and prevents small AI mistakes from turning into a completely confusing audiobook.

---

# 8. Initial Scope

The first version of Eliza Reader should remain deliberately small.

### V1

```text
URL
 ↓
Webpage
 ↓
Extract text
 ↓
Identify story
 ↓
Display clean story
```

### Later versions

```text
Clean story
 ↓
Characters
 ↓
Dialogue
 ↓
Speaker
 ↓
Voice assignment
 ↓
Narration planning
 ↓
TTS
 ↓
Real-time audiobook
```

The project should not move to the next stage until the previous stage works reliably.

---

## 9. Overall Boundary

In one sentence:

> **Eliza Reader receives a user-provided novel webpage, identifies and understands the story content within that webpage, creates a narration plan, and converts the story into spoken audio for the user's personal listening experience.**
