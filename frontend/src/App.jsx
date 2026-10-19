import { useEffect, useState } from "react";
import Home from "./pages/Home.jsx";
import Lecture from "./pages/Lecture.jsx";

const parse = () => {
  const m = window.location.hash.match(/^#\/lecture\/(\d+)/);
  return m ? Number(m[1]) : null;
};

export default function App() {
  const [id, setId] = useState(parse());

  useEffect(() => {
    const onChange = () => setId(parse());
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);

  return (
    <div className="shell">
      <header className="top">
        <a href="#/" className="brand">Lecture Highlighter</a>
      </header>
      <main>{id ? <Lecture id={id} /> : <Home />}</main>
    </div>
  );
}
