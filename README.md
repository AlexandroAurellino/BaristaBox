# BaristaBox AI ☕

**Version:** 2.0 (Rule-Based Hybrid Architecture)  
**Status:** The "Doctor" module is feature-complete and demonstrates the core architectural principles of the project.

---

## 📖 Project Overview

BaristaBox AI is a sophisticated expert system designed to act as a virtual coffee concierge, aiming to democratize the nuanced knowledge of professional baristas for home enthusiasts. The system assists users in diagnosing coffee brewing problems, discovering new beans, and receiving precise brewing recipes through an intuitive conversational interface.

This project was developed for an Expert Systems course, with a specific focus on implementing a hybrid architecture. This architecture thoughtfully combines the explainable logic of classic rule-based systems with the advanced conversational and understanding capabilities of modern Large Language Models (LLMs).

### Core Implemented Feature: The Coffee Doctor

The centerpiece of this project is **"The Doctor"**—a fully implemented, context-aware diagnostic assistant. It guides users through a step-by-step process to identify and solve common issues with their coffee brews, such as sourness, bitterness, or weakness. The other modules, "The Sommelier" and "The Master Brewer," are functional prototypes demonstrating alternative AI patterns.

## 🏛️ System Architecture: A Rule-Based, AI-Enhanced Model

The architecture of BaristaBox AI was deliberately refactored to address the principles of classic expert systems, resulting in a "Rule-Based, AI-Enhanced" model. This design ensures that the core reasoning is transparent and logically sound, while leveraging AI to create a seamless and intelligent user experience.

The system utilizes a total of **three computational models**: two locally-run PyTorch models for rapid classification and one cloud-based LLM (Google Gemini) for advanced reasoning and language generation.

---

### In-Depth Logic & Control Flow: The "Doctor" Module

The `doctor` module serves as the primary showcase of the hybrid architecture. Its logic has been explicitly designed to function as an explainable, rule-based inference engine, with the LLM acting as a sophisticated language interface rather than the core decision-maker.

Here is the detailed control flow for a typical diagnostic session:

**1. Initial Classification (The "Fast Brain")**
This stage uses locally-run, fine-tuned PyTorch models to rapidly structure the user's ambiguous input.

- **User Input:** A natural language complaint, e.g., `My V60 coffee tastes sour.`
- **Step 1: Intent Classification:** The input is processed by the **`Master Intent Classifier`**. This model's sole purpose is to categorize the user's high-level goal.
  - **Output:** `doctor`
- **Step 2: Problem Classification:** Because the intent is `doctor`, the same input is then processed by the **`Doctor Problem Classifier`**. This model identifies the specific issue.
  - **Output:** `sour`

**2. Context Gathering (The Expert's First Step)**
Before jumping to conclusions, the system, now in `doctor_chat` mode, mimics an expert by gathering critical context. This is a hard-coded, rule-based sequence.

- **Step 3: The engine asks for the coffee bean:** "What coffee bean are you brewing?"
  - **User provides:** `Ethiopia Yirgacheffe`
- **Step 4: The engine asks for the brew method:** "What brew method are you using?"
  - **User provides:** `V60`
- **Result:** The system now has a complete context: `{problem: 'sour', bean: 'Ethiopia Yirgacheffe', method: 'V60'}`. This context is essential for providing non-generic, expert-level advice.

**3. Rule-Based Inference (The Core Logic Engine)**
With the context established, the `doctor_engine` begins its deterministic, step-by-step diagnostic process, which is a classic example of **forward-chaining**.

- **Step 5: Load Rules:** The engine retrieves the list of potential `causes` for the `sour` problem from the `troubleshooting_knowledge_base.json` file. It creates an iterator to go through them one by one.

- **Step 6: Test Hypothesis #1 (`grind_coarse`):**

  - **Retrieve Rule:** The engine gets the first cause and its associated `question`.
  - **Phrase & Ask:** It uses the Gemini API as a **language formatter**, with a strict prompt: _"Ask the user this question in a friendly way: [question text]"_. The user is asked about their grind size.

- **Step 7: Interpret User Response (AI-Enhanced Understanding):**

  - **User Input:** An ambiguous, natural language answer, e.g., `not sure, more like breadcrumb i guess`.
  - **Interpret with LLM:** The engine sends this ambiguous answer and the original question to the Gemini API with a specific, constrained task: _"Interpret this user's response in the context of the question. Respond ONLY with one of these three words: 'affirmative', 'negative', or 'unsure'."_
  - **Structured Output:** The API returns a single, structured word: `affirmative`.

- **Step 8: Execute Action Based on Interpretation:**
  - **Rule Execution:** The Python code receives the `affirmative` interpretation. An `IF` condition (`if interpretation == 'affirmative'`) is met. The diagnostic loop concludes.
  - **Retrieve Solution:** The engine retrieves the `solution` text associated with the confirmed `grind_coarse` cause.
  - **Phrase & Conclude:** It uses the Gemini API one last time as a language formatter, providing it with the solution text and the full user context. The prompt is: _"Explain this solution in a helpful way, using the context that the user is brewing an Ethiopia Yirgacheffe with a V60."_
  - The final, tailored, and educational response is generated and displayed to the user.

### Architectural Justification

This design choice is deliberate. The **"what to do next"** logic—the core of the expert system's reasoning—is explicitly controlled by the Python code, making it transparent, deterministic, and traceable through logs. The **"how to say it"** task is delegated to the LLM, leveraging its power to create a user experience that is natural, empathetic, and far superior to a system that simply prints raw text from a database. This creates a powerful and explainable hybrid system that honors the principles of classic expert systems while embracing the capabilities of modern AI.```
