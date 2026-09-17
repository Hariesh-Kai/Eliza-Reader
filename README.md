# Eliza Reader

## 1. Purpose of the Application

The purpose of **Eliza Reader** is to allow me to listen to my favorite novel, ***Losing Money to Be a Tycoon***, when I am unable to sit down and read it myself.

There are situations where I cannot read the novel, such as while I am at the office or when I am busy at home. Because I still want to experience the story, I am building Eliza Reader to make the novel accessible through natural audio narration.

The initial goal is simple:

**Instead of me reading the novel, Eliza Reader should read it to me.**

This is primarily a personal-use application. The novel itself is not the product being developed or distributed. The application is the project.

---

## 2. How the Application Should Work

I will provide **Eliza Reader with the website link containing the novel/chapter**.

The application should then:

1. Open the provided website.
2. Scan the contents of the webpage.
3. Determine which parts of the webpage contain the actual novel/story.
4. Ignore things that are not part of the story, such as:

   * Website headers
   * Navigation menus
   * Footer
   * Advertisements
   * Buttons
   * Comments
   * Other unrelated webpage content
5. Identify the chapter and extract the actual story text.
6. Analyze the extracted story.
7. Identify characters and dialogue.
8. Determine who is speaking when possible.
9. Create a narration plan.
10. Begin reading the story aloud.

The application should not simply read every piece of text found on the webpage.

Its first responsibility is to understand:

> **"Which text on this webpage is actually the novel?"**

---

## 3. The Reading Experience

Eliza Reader should eventually behave more like an audiobook narrator than a basic text-to-speech reader.

It should understand the difference between:

**Narration**

and

**Character dialogue.**

For example, if the novel contains narration followed by dialogue, Eliza Reader should determine who is speaking and use the appropriate character voice.

The voice does not have to match the biological gender of the character.

For example:

**Male protagonist → Female voice**

This is intentional. Character voice assignment should be controlled by Eliza Reader's narration plan rather than automatically assuming that male characters must use male voices and female characters must use female voices.

---

## 4. Character Understanding

Eliza Reader should scan the chapter and identify the characters appearing in the story.

For each character, the system should eventually be able to maintain information such as:

* Character name
* Role in the story
* Voice assigned to the character
* Speaking style
* Typical speed
* Other relevant narration characteristics

Once a voice has been assigned to a character, the same character should preferably continue using the same voice throughout the novel.

This is important for maintaining a consistent listening experience.

---

## 5. Understanding Dialogue

Eliza Reader should identify dialogue within the story.

It should determine:

* Where dialogue begins and ends
* Who is speaking
* Whether the text is narration or dialogue
* The surrounding context
* How the dialogue should be delivered

For example:

```text
Narration
    ↓
Character A speaks
    ↓
Narration
    ↓
Character B responds
    ↓
Narration
```

The application should convert this into an appropriate sequence of spoken audio.

---

## 6. Understanding How the Story Should Be Read

Eliza Reader should eventually understand that every sentence does not need to be spoken at the same speed or with the same delivery.

The system should be able to determine appropriate:

* Speaking speed
* Pauses
* Emphasis
* Emotional delivery
* Dialogue delivery
* Narration delivery

For example, an exciting scene may be read differently from a calm scene.

A character who is angry should not necessarily sound identical to the same character when they are relaxed.

The goal is to make the reading feel like a **performed story**, rather than a machine simply converting text into speech.

---

## 7. Real-Time Reading

Eliza Reader should eventually read the novel in real time.

It should not necessarily wait for the entire novel to be processed before starting.

The intended workflow is:

```text
Website
   ↓
Extract chapter
   ↓
Understand story
   ↓
Create narration plan
   ↓
Start reading
   ↓
Continue analyzing upcoming text
   ↓
Continue reading
```

This should allow the application to prepare upcoming portions while the current portion is being spoken.

---

## 8. Development Philosophy

Eliza Reader will be developed gradually.

The first version should **not** attempt to solve everything at once.

The development should begin with the simplest possible problem:

```text
Website URL
      ↓
Extract webpage contents
      ↓
Identify actual novel text
      ↓
Output clean story text
```

Once this works reliably, additional capabilities can be added:

```text
Clean story text
      ↓
Character detection
      ↓
Dialogue detection
      ↓
Speaker identification
      ↓
Voice assignment
      ↓
Emotion/context understanding
      ↓
Speed and pause planning
      ↓
Text-to-speech
      ↓
Real-time narration
```

Each stage should be tested before moving to the next stage.

---

## 9. The Core Vision

The core vision of Eliza Reader is:

> **Give it a novel webpage, let it understand the webpage and the story, and then let it read the story to me naturally.**

The application should ultimately feel like having a personal AI audiobook narrator that can understand the story rather than simply reading webpage text mechanically.

The initial motivation is simple:

**I want to experience *Losing Money to Be a Tycoon* even when I cannot physically sit down and read it.**

That is why Eliza Reader exists.
