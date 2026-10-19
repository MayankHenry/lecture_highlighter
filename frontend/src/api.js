const json = async (r) => {
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    throw new Error(body.detail || r.statusText);
  }
  return r.json();
};

export const listLectures = () => fetch("/api/lectures").then(json);
export const getLecture = (id) => fetch(`/api/lectures/${id}`).then(json);
export const uploadLecture = (file, title) => {
  const form = new FormData();
  form.append("file", file);
  form.append("title", title);
  return fetch("/api/lectures", { method: "POST", body: form }).then(json);
};
