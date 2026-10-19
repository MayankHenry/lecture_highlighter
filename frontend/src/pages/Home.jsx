import { useEffect, useState } from "react";
import { listLectures, uploadLecture } from "../api.js";

const STATUS = {
  queued: "Queued",
  uploading: "Uploading",
  transcribing: "Transcribing",
  chaptering: "Finding chapters",
  ready: "Ready",
  failed: "Failed",
};

export default function Home() {
  const [lectures, setLectures] = useState([]);
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    listLectures().then(setLectures).catch((err) => setLoadError(err.message));
  }, []);

  async function submit(e) {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const lec = await uploadLecture(file, title);
      window.location.hash = `#/lecture/${lec.id}`;
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <div className="home">
      <section className="intro">
        <h1>Turn a lecture into chapters, notes, and short clips.</h1>
        <p>Upload a recording. You get a chapter for each topic, study notes, and a clip you can share for each chapter.</p>
      </section>

      <form className="upload" onSubmit={submit}>
        <label className="field">
          <span>Lecture video or audio</span>
          <input type="file" accept="video/*,audio/*" onChange={(e) => setFile(e.target.files[0] || null)} />
        </label>
        <label className="field">
          <span>Title</span>
          <input type="text" value={title} placeholder="Lecture 4: Binary trees" onChange={(e) => setTitle(e.target.value)} />
        </label>
        <button className="btn" disabled={!file || busy}>{busy ? "Uploading…" : "Create chapters"}</button>
        {error && <p className="error" role="alert">{error}</p>}
      </form>

      <section className="recent">
        <h2>Your lectures</h2>
        {loadError ? (
          <p className="error" role="alert">{loadError}</p>
        ) : lectures.length === 0 ? (
          <p className="muted">Nothing here yet. Upload your first lecture above.</p>
        ) : (
          <ul>
            {lectures.map((l) => (
              <li key={l.id}>
                <a href={`#/lecture/${l.id}`}>
                  <span className="rtitle">{l.title}</span>
                  <span className={`pill ${l.status}`}>{STATUS[l.status] || l.status}</span>
                </a>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
