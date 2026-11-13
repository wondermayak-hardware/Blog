"""Daily blog generator: picks next idea -> OpenRouter writes body -> sends to Telegram."""
import os, re, json, sys, html, datetime
from pathlib import Path
import requests

ROOT = Path(__file__).parent
STATE = ROOT / "state.json"
IDEAS = json.loads((ROOT / "ideas.json").read_text(encoding="utf-8"))

OR_KEY = os.environ.get("OPENROUTER_API_KEY", "")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
TEST_URL = os.environ.get("TEST_URL", "https://thundertest.indevs.in")
STUDY_URL = os.environ.get("STUDY_URL", "https://thunderstudy.indevs.in")
LANGUAGE = os.environ.get("LANGUAGE", "simple English")
# Optional override (comma-separated). Leave empty: free models are discovered automatically.
MODELS = [m.strip() for m in os.environ.get("MODELS", "").split(",") if m.strip()]
DRY = os.environ.get("DRY_RUN") == "1"

SYSTEM = ("You are an expert Indian exam-prep content writer for CUET students. You write accurate, student-friendly, "
          "original blog posts. Output ONLY an HTML fragment for the Blogger post editor: no <html>, <head>, <body>, "
          "<title>, <h1>, markdown, or code fences. Use only <h2>, <h3>, <p>, <ul>, <ol>, <li>, <b>, <i>, <br>. "
          "Never add external links. Only state facts you are sure are correct; avoid time-sensitive claims.")

def prompt_for(idea):
    t, topic, subj = idea["title"], idea["topic"], idea["subject"]
    if idea["type"] == "questions":
        body = (f"Blog title: {t}\nSubject: {subj} / {topic}\nLanguage: {LANGUAGE}\n\n"
                "Write the post with:\n"
                "1. A 2-3 sentence intro (use the main keyword once).\n"
                "2. A short 'How to use this set' tip.\n"
                "3. Exactly 10 MCQs at CUET level (match the difficulty in the title). Format each as: "
                "<p><b>Q1.</b> question</p> then an <ol type=\"a\"> with 4 options. Vary the correct option.\n"
                "4. An <h2>Answer Key with Explanations</h2> section: for each Q, '<p><b>Q1. Answer: (b) text</b> - one-line explanation</p>'.\n"
                "5. An <h2>Quick Tips</h2> section with 4 bullets.\n"
                "Make every question different from common textbook examples.")
    else:
        body = (f"Blog title: {t}\nSubject: {subj} / {topic}\nLanguage: {LANGUAGE}\n\n"
                "Write 900-1200 words: intro (use main keyword once), 5-6 <h2> sections with practical, specific advice, "
                "a simple day-wise or step-wise plan where relevant, 3 example practice questions with answers, "
                "and an <h2>FAQs</h2> section with 4 short Q&As. Keep it motivating and honest; do not promise results.")
    return body

GOOD = ("nemotron", "llama", "qwen", "deepseek", "gemini", "gemma", "mistral", "gpt-oss", "glm", "kimi", "minimax", "laguna", "mimo")
BAD = ("embed", "rerank", "guard", "image", "audio", "vision", "-vl", "tts", "whisper", "moderation", "stealth")

def discover_free_models(limit=8):
    """Reads OpenRouter's public model list and returns currently free text models, best first."""
    try:
        data = requests.get("https://openrouter.ai/api/v1/models", timeout=30).json().get("data", [])
    except Exception as e:
        print("model discovery failed:", e); return []
    found = []
    for m in data:
        mid = m.get("id", "").lower()
        p = m.get("pricing") or {}
        try:
            free = float(p.get("prompt", 1)) == 0 and float(p.get("completion", 1)) == 0
        except (TypeError, ValueError):
            free = False
        arch = m.get("architecture") or {}
        text_out = "text" in (arch.get("output_modalities") or ["text"])
        if not free or not text_out or any(b in mid for b in BAD) or mid.startswith("openrouter/"):
            continue
        ctx = m.get("context_length") or 0
        if ctx < 32000:
            continue
        score = (any(g in mid for g in GOOD), mid.endswith(":free"), min(ctx, 262144), m.get("created") or 0)
        found.append((score, m["id"]))
    found.sort(reverse=True)
    return [mid for _, mid in found[:limit]]

def call_model(prompt):
    # order: your override -> auto-discovered free models -> OpenRouter's own free router
    models = MODELS + [m for m in discover_free_models() if m not in MODELS] + ["openrouter/free"]
    print("trying models:", models)
    last = None
    for model in models:
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OR_KEY}", "HTTP-Referer": STUDY_URL, "X-Title": "ThunderStudy Blog Bot"},
                json={"model": model, "temperature": 0.7, "max_tokens": 6000,
                      "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]},
                timeout=240)
            r.raise_for_status()
            raw = (r.json()["choices"][0]["message"].get("content") or "")
            text = clean(raw)
            ok = len(text) > 1500 and "<h2" in text
            if ok and "Answer" in prompt and "Answer" not in text:
                ok = False
            if ok:
                return text, model
            last = f"{model}: output too short or incomplete"
        except Exception as e:
            last = f"{model}: {e}"
        print("skip", last)
    raise RuntimeError(last or "no models available")

def clean(t):
    t = re.sub(r"^```(?:html)?\s*|\s*```$", "", t.strip())
    t = re.sub(r"(?is)<!doctype.*?>|</?(html|head|body)[^>]*>|<title>.*?</title>|<h1[^>]*>.*?</h1>", "", t)
    return t.strip()

def cta():
    box = ("background:#eef3fb;border-radius:18px;padding:18px 20px;margin:28px 0;font-family:inherit;")
    btn = ("display:inline-block;background:#7897D1;color:#ffffff;padding:10px 20px;border-radius:999px;"
           "text-decoration:none;font-weight:bold;margin:6px 8px 0 0;")
    return (f'<div style="{box}"><p style="margin:0 0 6px;"><b style="color:#111;">Practice more for free on ThunderStudy</b></p>'
            f'<p style="margin:0 0 8px;color:#111;">Take free CUET mock tests and previous year question practice, no signup needed.</p>'
            f'<a href="{TEST_URL}" style="{btn}">Free Mock Tests</a>'
            f'<a href="{STUDY_URL}" style="{btn}">ThunderStudy</a></div>')

def meta_description(body):
    m = re.search(r"(?is)<p[^>]*>(.*?)</p>", body)
    text = re.sub(r"<[^>]+>", "", m.group(1)) if m else ""
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    return text[:150].rsplit(" ", 1)[0] + "..." if len(text) > 150 else text

def tg(method, data=None, files=None):
    r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/{method}", data=data, files=files, timeout=60)
    r.raise_for_status()

def main():
    state = json.loads(STATE.read_text()) if STATE.exists() else {"next": 0, "history": []}
    if state["next"] >= len(IDEAS):
        if not DRY: tg("sendMessage", {"chat_id": TG_CHAT, "text": "All 5000 blog ideas are used. Time to generate a new list."})
        return
    idea = IDEAS[state["next"]]
    try:
        if DRY:
            body, model = "<h2>Test</h2><p>Dry run body. " + "x " * 800 + "</p>", "dry-run"
        else:
            body, model = call_model(prompt_for(idea))
    except Exception as e:
        if not DRY: tg("sendMessage", {"chat_id": TG_CHAT, "text": f"Blog bot failed for idea #{idea['id']}: {str(e)[:300]}\nIt will retry tomorrow with the same idea."})
        print("FAILED:", e); sys.exit(1)

    post = body + "\n" + cta()
    desc = meta_description(body)
    labels = ", ".join(idea["labels"])
    header = f"Blog #{idea['id']}/{len(IDEAS)}\n\nTitle:\n{idea['title']}\n\nLabels:\n{labels}\n\nSearch description:\n{desc}\n\nPaste the file into Blogger > Compose post > HTML view."
    if DRY:
        out = ROOT / "out"; out.mkdir(exist_ok=True)
        (out / f"blog-{idea['id']}.txt").write_text(post, encoding="utf-8"); print(header); return
    tg("sendMessage", {"chat_id": TG_CHAT, "text": header})
    name = f"blog-{idea['id']}"
    tg("sendDocument", {"chat_id": TG_CHAT, "caption": "Copy this text, paste in Blogger HTML view"}, {"document": (f"{name}.txt", post.encode("utf-8"))})
    tg("sendDocument", {"chat_id": TG_CHAT, "caption": "Preview (open in browser)"}, {"document": (f"{name}.html", post.encode("utf-8"))})
    state["next"] += 1
    state["history"] = (state["history"] + [{"id": idea["id"], "title": idea["title"], "date": datetime.date.today().isoformat(), "model": model}])[-30:]
    STATE.write_text(json.dumps(state, indent=1), encoding="utf-8")

if __name__ == "__main__":
    main()
