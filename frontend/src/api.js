const json = async (response) => {
  let body;
  try {
    body = await response.json();
  } catch {
    if (response.ok) throw new Error("The server returned an unreadable response. Please try again.");
    body = {};
  }

  if (!response.ok) {
    if (response.status >= 500) {
      throw new Error("The server encountered a problem. Please try again, and check the backend logs if it continues.");
    }
    if (typeof body.detail === "string") throw new Error(body.detail);
    if (response.status === 404) throw new Error("We couldn't find that lecture. It may have been deleted.");
    if (response.status === 413) throw new Error("This file is too large to upload. Try a smaller file.");
    throw new Error("The request could not be completed. Check the information and try again.");
  }
  return body;
};

const request = async (url, options) => {
  let response;
  try {
    response = await fetch(url, options);
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error("Can't connect to the backend. Make sure the API server is running on port 8000.");
    }
    throw error;
  }
  return json(response);
};

export const listLectures = () => request("/api/lectures");
export const getLecture = (id) => request(`/api/lectures/${id}`);
export const uploadLecture = (file, title) => {
  const form = new FormData();
  form.append("file", file);
  form.append("title", title);
  return request("/api/lectures", { method: "POST", body: form });
};
