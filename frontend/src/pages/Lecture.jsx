import { useEffect, useRef, useState } from "react";
import { getLecture } from "../api.js";

const STEPS = [
  ["uploading", "Uploading to Cloudinary"],
  ["transcribing", "Transcribing the speech"],
  ["chaptering", "Finding chapters"],
];

const fmt = (s) => {
  s = Math.floor(s);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = String(s % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${sec}` : `${m}:${sec}`;
};

export default function Lecture({ id }) {
  const [lec, setLec] = useState(null);
  const [error, setError] = useState("");
  const [time, setTime] = useState(0);
  const [clipIdx, setClipIdx] = useState(null);
  const video = useRef(null);
  const pending = useRef(null);

  useEffect(() => {
    let stop = false;
    let timer;
    const load = async () => {
      try {
        const data = await getLecture(id);
        if (stop) return;
        setLec(data);
        if (data.status !== "ready" && data.status !== "failed") timer = setTimeout(load, 3000);
      } catch (e) {
        if (!stop) setError(e.message);
      }
    };
    load();
    return () => {
      stop = true;
      clearTimeout(timer);
    };
  }, [id]);

  if (error) return <p className="error" role="alert">{error}</p>;
  if (!lec) return <p className="muted">Loading…</p>;

  if (lec.status === "failed") {
    return (
      <div className="state">
        <h1>{lec.title}</h1>
        <p className="error" role="alert">Processing failed: {lec.error}</p>
        <a className="btn" href="#/">Try another lecture</a>
      </div>
    );
  }

  if (lec.status !== "ready") {
    const current = STEPS.findIndex(([k]) => k === lec.status);
    return (
      <div className="state">
        <h1>{lec.title}</h1>
        <p className="muted">This takes a few minutes for longer lectures. You can leave this page open.</p>
        <ol className="steps">
          {STEPS.map(([k, label], i) => (
            <li key={k} className={i < current ? "done" : i === current ? "now" : ""}>{label}</li>
          ))}
        </ol>
      </div>
    );
  }

  const chapters = lec.chapters;
  const timeIdx = chapters.reduce((a, c, i) => (time >= c.start ? i : a), 0);
  const active = clipIdx !== null ? clipIdx : timeIdx;
  const chapter = chapters[active];
  const src = clipIdx !== null ? chapters[clipIdx].clip_url : lec.video_url;

  function seek(c) {
    if (clipIdx !== null) {
      pending.current = c.start;
      setClipIdx(null);
      return;
    }
    video.current.currentTime = c.start;
    video.current.play();
  }

  function onLoaded(e) {
    if (pending.current != null) {
      e.currentTarget.currentTime = pending.current;
      e.currentTarget.play();
      pending.current = null;
    }
  }

  return (
    <div className="lecture">
      <div className="stage">
        <h1>{lec.title}</h1>
        <video
          key={src}
          ref={video}
          src={src}
          controls
          autoPlay={clipIdx !== null}
          onTimeUpdate={(e) => setTime(e.currentTarget.currentTime)}
          onLoadedMetadata={onLoaded}
        />

        {clipIdx !== null ? (
          <p className="clipbar">
            Playing the clip for “{chapter.title}”.{" "}
            <button className="link" onClick={() => seek(chapter)}>Back to full lecture</button>
          </p>
        ) : (
          <div className="timeline" role="group" aria-label="Chapters">
            {chapters.map((c, i) => (
              <button
                key={c.idx}
                className={i === active ? "seg on" : "seg"}
                style={{ flexGrow: Math.max(c.end - c.start, 1) }}
                title={`${c.title} (${fmt(c.start)})`}
                aria-label={`Jump to ${c.title}`}
                onClick={() => seek(c)}
              />
            ))}
          </div>
        )}

        <section className="notes">
          <h2><span className="hl">{chapter.title}</span></h2>
          <p className="summary">{chapter.summary}</p>
          {chapter.notes.length > 0 && (
            <ul>{chapter.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
          )}
        </section>
      </div>

      <aside className="chapters">
        <h2>{chapters.length} chapters</h2>
        <ul>
          {chapters.map((c, i) => (
            <li key={c.idx} className={i === active ? "active" : ""}>
              <button className="chapter" onClick={() => seek(c)}>
                <span className="time">{fmt(c.start)}</span>
                <span className="ctitle"><span className={i === active ? "hl" : ""}>{c.title}</span></span>
              </button>
              <div className="actions">
                <button className="link" onClick={() => { pending.current = null; setClipIdx(i); }}>Play clip</button>
                <a className="link" href={c.clip_url} target="_blank" rel="noreferrer">Open clip link</a>
              </div>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}
