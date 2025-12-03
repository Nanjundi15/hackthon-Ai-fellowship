# hackthon-Ai-fellowship

# 🚀 BrandMorpher: The Auto-Creative Engine

**Tagline:** Instantly generate 10+ brand-ready ad creatives using AI-powered layouts, captions, and image synthesis — all in under 20 seconds.

---

## 1. The Problem (Real-World Scenario)

In digital marketing teams, designers spend **hours** creating repetitive ad variations for performance testing (A/B testing, geo-personalization, seasonal creatives, etc.).

### The Pain Point

* Creating **10–20 creative variations** manually takes hours.
* Designers repeat the same workflow:
  *remove background → adjust layout → add logo → add caption → export JPGs*
* Marketers cannot scale fast enough, especially when running multiple campaigns.

### My Solution

I built **BrandMorpher**, an AI-powered creative engine that:

* Accepts a **brand logo** + **product image**
* Uses **Gemini AI** to generate captions and creative variations
* Automatically produces **10+ high-quality ad creatives**
* Packages everything into a single downloadable **ZIP file**

You simply upload two images, click **Generate**, and your ad kit is ready.

---

## 2. Expected End Result

### **For the User:**

**Input:**

* Brand Logo (PNG/JPG)
* Product Image (PNG/JPG)

**Action:**

* Click **Generate Creatives**

**Output:**
A ZIP file containing:

* 12 professionally designed ad creatives
* AI-generated catchy marketing captions
* Optional: AI-generated product renders (Gemini Image Model)
* A `captions.txt` file mapping each creative to its caption

---

## 3. Technical Approach

### **Goal:** Build a production-grade creative automation system with AI, strong fallback behavior, and complete reliability.

---

## System Architecture

### 1. **Frontend (Upload + Preview UI)**

* Drag-and-Drop support
* Live preview of uploaded images
* Progress loader during generation

### 2. **Backend (Flask Application)**

* Saves each run inside `/runs/<uuid>`
* Fully offline-safe (always generates creatives even without API keys)

### 3. **Creative Engine**

* Background removal + compositing (Pillow)
* Auto layout positioning using rule-based engine
* 12 creative templates rendered at 1200×1200 resolution

### 4. **AI Integration (Gemini API)**

#### **AI Image Generator**

Uses Google Gemini’s image model to generate additional product photos:

* Prompt: “Product photo of *ProductName* by *BrandName*”
* Returns 1024×1024 high-resolution images
* Falls back to placeholder images if API unavailable

#### **AI Caption Generator**

Uses Gemini 1.5 Mini to generate:

* 12 short, punchy marketing captions
* Tone similar to a performance marketer
* Few-shot prompting + guardrails

If Gemini is not available → uses deterministic template captions.

---

## 4. Tech Stack

### **Language**

* Python 3.11

### **Framework**

* Flask (Backend Web App)

### **AI**

* Google Gemini 1.5 Mini (via `google-generativeai`)

### **Image Processing**

* Pillow
* Custom layout composer

### **UX**

* Bootstrap + Vanilla JS
* Live previews + drag-drop uploads

### **Packaging**

* ZIP export with embedded creatives and captions

---

## 5. Challenges & Learnings

### **Challenge 1: AI API Variability**

Gemini SDK versions differ (some use `generate_text`, others `images.generate`).
**Fix:** Wrote a defensive adapter that:

* Tries multiple generation methods
* Auto-fallback to placeholders
* Ensures the system never breaks on demo day

### **Challenge 2: Asynchronous UX**

Users need to understand the process is running.
**Fix:** Added:

* Disable buttons during generation
* Live “Processing…” banner
* Clear previews button

### **Challenge 3: Layout Automation**

Ad creatives require consistency.
**Fix:** Built a modular layout engine:

* Auto logo placement
* Auto caption placement
* Background styling
* Consistent padding/margins

---

## 6. Visual Proof

Your README will show images here when you upload:

* **Sample Output Creatives**
* **Gemini Generated Images**
* **UI Screen (Upload + Preview)**

*(Add screenshots during your hackathon demo.)*

---

## 7. How to Run

### **1. Clone the Repository**

```bash
git clone https://github.com/username/brandmorpher.git
cd brandmorpher
```

### **2. Create Virtual Environment**

```bash
python -m venv venv
venv\Scripts\Activate.ps1   # Windows
```

### **3. Install Requirements**

```bash
pip install -r requirements.txt
pip install google-generativeai python-dotenv
```

### **4. Add API Key**

Create `.env`:

```
FLASK_SECRET=dev_secret
USE_LLM=true
USE_IMAGE_API=true
GEMINI_API_KEY="your_key_here"
```

### **5. Run the App**

```bash
python app.py
```

### **6. Open in Browser**

```
http://127.0.0.1:5000/
```

Upload your **NEXORA Logo** + **Product Image** → Click **Generate** → Done!

---


