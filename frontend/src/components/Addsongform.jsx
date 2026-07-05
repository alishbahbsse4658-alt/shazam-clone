/*
  AddSongForm.jsx
  ---------------
  Ye form 2 tareeqon se song add karne deta hai:
  1. "Upload" tab - MP3/WAV file seedha upload karna
  2. "YouTube" tab - koi YouTube link paste karna

  Dono cases mein backend ka alag endpoint call hota hai, lekin
  UI/UX ekjaisa rehta hai.
*/

import { useState } from "react";
import "./AddSongForm.css";

const BACKEND_URL = "http://localhost:5000";

function AddSongForm({ onSongAdded }) {
  // activeTab: "upload" | "youtube"
  const [activeTab, setActiveTab] = useState("upload");

  const [title, setTitle] = useState("");
  const [artist, setArtist] = useState("");
  const [file, setFile] = useState(null);
  const [youtubeUrl, setYoutubeUrl] = useState("");

  // status: "idle" | "loading" | "success" | "error"
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("");

  function resetFormFields() {
    setTitle("");
    setArtist("");
    setFile(null);
    setYoutubeUrl("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setStatus("loading");
    setMessage("");

    try {
      let response;

      if (activeTab === "upload") {
        if (!file) {
          setStatus("error");
          setMessage("Pehle koi audio file chunein.");
          return;
        }

        const formData = new FormData();
        formData.append("file", file);
        formData.append("title", title || file.name);
        formData.append("artist", artist || "Unknown Artist");

        response = await fetch(`${BACKEND_URL}/add-song`, {
          method: "POST",
          body: formData,
        });
      } else {
        if (!youtubeUrl) {
          setStatus("error");
          setMessage("Pehle YouTube link daalein.");
          return;
        }

        response = await fetch(`${BACKEND_URL}/add-song-youtube`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            url: youtubeUrl,
            title: title || "Unknown Title",
            artist: artist || "Unknown Artist",
          }),
        });
      }

      const data = await response.json();

      if (!response.ok) {
        // Backend se aaya hua error message dikhana
        // (jaise "Database full hai!" ya koi aur wajah)
        setStatus("error");
        setMessage(data.error || "Kuch ghalat ho gaya.");
        return;
      }

      setStatus("success");
      setMessage(`"${data.title}" successfully add ho gaya.`);
      resetFormFields();

      // Parent (App.jsx) ko batana ke ek naya song add hua hai,
      // taake wo counter ko refresh kar sake
      onSongAdded();
    } catch (error) {
      setStatus("error");
      setMessage("Backend se connect nahi ho saka. Kya server chal raha hai?");
    }
  }

  return (
    <section className="add-song-card">
      <h2 className="add-song-title">Add new songs</h2>

      {/* Tab switcher */}
      <div className="tab-switcher" role="tablist">
        <button
          role="tab"
          aria-selected={activeTab === "upload"}
          className={`tab-button ${activeTab === "upload" ? "tab-button--active" : ""}`}
          onClick={() => setActiveTab("upload")}
          type="button"
        >
          Upload file
        </button>
        <button
          role="tab"
          aria-selected={activeTab === "youtube"}
          className={`tab-button ${activeTab === "youtube" ? "tab-button--active" : ""}`}
          onClick={() => setActiveTab("youtube")}
          type="button"
        >
          YouTube link
        </button>
      </div>

      <form onSubmit={handleSubmit} className="add-song-form">
        {activeTab === "upload" ? (
          <label className="file-drop">
            <input
              type="file"
              accept="audio/*"
              onChange={(e) => setFile(e.target.files[0])}
              hidden
            />
            <span className="file-drop__text">
              {file ? file.name : "Choose an audio file (MP3, WAV)"}
            </span>
          </label>
        ) : (
          <input
            type="text"
            className="text-input"
            placeholder="https://www.youtube.com/watch?v=..."
            value={youtubeUrl}
            onChange={(e) => setYoutubeUrl(e.target.value)}
          />
        )}

        <div className="form-row">
          <input
            type="text"
            className="text-input"
            placeholder="Song title (optional)"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <input
            type="text"
            className="text-input"
            placeholder="Artist (optional)"
            value={artist}
            onChange={(e) => setArtist(e.target.value)}
          />
        </div>

        <button type="submit" className="submit-button" disabled={status === "loading"}>
          {status === "loading" ? "Adding..." : "Submit"}
        </button>
      </form>

      {message && (
        <p className={`form-message form-message--${status}`}>{message}</p>
      )}
    </section>
  );
}

export default AddSongForm;