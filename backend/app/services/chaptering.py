"""LangGraph pipeline: transcript -> windows -> topic boundaries -> titled chapters -> validated."""
import json
import re
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app import config

WINDOW_SECONDS = 60
MIN_CHAPTER_SECONDS = 20
FALLBACK_WINDOWS_PER_CHAPTER = 3


class State(TypedDict, total=False):
    segments: list[dict]
    duration: float
    windows: list[dict]
    boundaries: list[int]
    chapters: list[dict]


def _ask(prompt: str):
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=config.LLM_MODEL,
        api_key=config.LLM_API_KEY,
        base_url=config.LLM_BASE_URL or None,
        temperature=0.2,
        timeout=120,
        max_retries=2,
    )
    text = llm.invoke(prompt).content or ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    text = re.sub(r"```(?:json)?", "", text)
    match = re.search(r"(\[.*\]|\{.*\})", text, flags=re.S)
    return json.loads(match.group(1))


def split_transcript(state: State):
    windows: list[dict] = []
    cur = None
    for s in state["segments"]:
        if cur is None or s["start"] - cur["start"] >= WINDOW_SECONDS:
            cur = {"i": len(windows), "start": s["start"], "end": s["end"], "text": ""}
            windows.append(cur)
        cur["end"] = s["end"]
        cur["text"] += " " + s["text"]
    return {"windows": windows}


def detect_topics(state: State):
    windows = state["windows"]
    fallback = list(range(0, len(windows), FALLBACK_WINDOWS_PER_CHAPTER))
    if not windows or not config.LLM_API_KEY:
        return {"boundaries": fallback}
    listing = "\n".join(f"[{w['i']}] ({int(w['start'])}s) {w['text'][:400]}" for w in windows)
    prompt = (
        "You split a lecture transcript into topic chapters. Each line below is a one-minute "
        "window with its index. Return ONLY a JSON array of window indexes where a new topic "
        "begins (it must include 0). Aim for one chapter every 3-8 minutes.\n\n" + listing
    )
    try:
        raw = _ask(prompt)
        bounds = sorted({int(x) for x in raw if 0 <= int(x) < len(windows)} | {0})
        return {"boundaries": bounds}
    except Exception:
        return {"boundaries": fallback}


def title_and_summarize(state: State):
    windows, bounds = state["windows"], state["boundaries"]
    chapters = []
    for n, start_i in enumerate(bounds):
        end_i = bounds[n + 1] if n + 1 < len(bounds) else len(windows)
        group = windows[start_i:end_i]
        text = " ".join(w["text"] for w in group).strip()
        ch = {
            "start": group[0]["start"],
            "end": group[-1]["end"],
            "title": f"Part {n + 1}",
            "summary": text[:200],
            "notes": [],
        }
        if config.LLM_API_KEY:
            try:
                out = _ask(
                    'Return ONLY JSON: {"title": "max 8 words", "summary": "1-2 sentences", '
                    '"notes": ["3-5 concise study bullet points"]}\n\nLecture excerpt:\n' + text[:6000]
                )
                ch["title"] = str(out.get("title", ch["title"]))[:200]
                ch["summary"] = str(out.get("summary", ch["summary"]))
                ch["notes"] = [str(x) for x in out.get("notes", [])][:6]
            except Exception:
                pass
        chapters.append(ch)
    return {"chapters": chapters}


def validate_timestamps(state: State):
    merged: list[dict] = []
    for ch in state["chapters"]:
        if merged and ch["end"] - ch["start"] < MIN_CHAPTER_SECONDS:
            merged[-1]["end"] = ch["end"]
            continue
        merged.append(ch)
    for a, b in zip(merged, merged[1:]):
        a["end"] = b["start"]
    if merged:
        merged[0]["start"] = 0.0
        merged[-1]["end"] = state["duration"]
    return {"chapters": merged}


def _build():
    g = StateGraph(State)
    g.add_node("split_transcript", split_transcript)
    g.add_node("detect_topics", detect_topics)
    g.add_node("title_and_summarize", title_and_summarize)
    g.add_node("validate_timestamps", validate_timestamps)
    g.set_entry_point("split_transcript")
    g.add_edge("split_transcript", "detect_topics")
    g.add_edge("detect_topics", "title_and_summarize")
    g.add_edge("title_and_summarize", "validate_timestamps")
    g.add_edge("validate_timestamps", END)
    return g.compile()


_graph = _build()


def make_chapters(segments: list[dict], duration: float) -> list[dict]:
    return _graph.invoke({"segments": segments, "duration": duration})["chapters"]
