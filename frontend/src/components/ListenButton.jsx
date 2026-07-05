/*
  ListenButton.jsx
  ----------------
  Ye app ka "signature" element hai - ek button jo:
  1. Tap hone par mic se audio record karta hai
  2. Recording ke dauran pulsing rings dikhata hai (jaise sound waves)
  3. Recording khatam hone par backend ko audio bhejta hai (/identify)
  4. Result (song mila / nahi mila) dikhata hai

  4 states hain is button ke: idle -> listening -> identifying -> result
*/

import { useState, useRef } from "react";
import "./ListenButton.css";

const BACKEND_URL = "http://localhost:5000";
const RECORD_DURATION_MS = 8000; // 8 second ka clip record karenge

function ListenButton() {
  // status: "idle" | "listening" | "identifying" | "result"
  const [status, setStatus] = useState("idle");
  const [result, setResult] = useState(null); // { match, title, artist, confidence }
  const [errorMessage, setErrorMessage] = useState(null);

  // useRef isliye use kar rahe hain kyunke ye values re-render
  // trigger nahi karni chahiye, bas record karte waqt store honi hain
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  async function handleListenClick() {
    // Agar already sun raha hai ya process kar raha hai, dobara click ignore karo
    if (status === "listening" || status === "identifying") return;

    setErrorMessage(null);
    setResult(null);

    try {
      // Browser se mic permission maangna aur audio stream lena
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // Jab bhi audio ka chunk (tukda) ready ho, usay collect karo
      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      // Jab recording ruk jaye (stop() call hone par), ye chalega
      mediaRecorder.onstop = async () => {
        // Sab chunks ko jod kar ek audio file (Blob) banana
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });

        // Mic ka use khatam - taake browser ka "recording" indicator hat jaye
        stream.getTracks().forEach((track) => track.stop());

        await sendToBackend(audioBlob);
      };

      mediaRecorder.start();
      setStatus("listening");

      // Fixed duration ke baad khud hi recording rok dena
      setTimeout(() => {
        if (mediaRecorder.state !== "inactive") {
          mediaRecorder.stop();
        }
      }, RECORD_DURATION_MS);
    } catch (error) {
      setErrorMessage("Mic access nahi mila. Browser permissions check karein.");
      setStatus("idle");
    }
  }

  async function sendToBackend(audioBlob) {
    setStatus("identifying");

    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");

    try {
      const response = await fetch(`${BACKEND_URL}/identify`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      setResult(data);
      setStatus("result");
    } catch (error) {
      setErrorMessage("Backend se connect nahi ho saka. Kya server chal raha hai?");
      setStatus("idle");
    }
  }

  function handleReset() {
    setStatus("idle");
    setResult(null);
    setErrorMessage(null);
  }

  return (
    <div className="listen-section">
      <button
        className={`listen-button listen-button--${status}`}
        onClick={status === "result" ? handleReset : handleListenClick}
        aria-label={status === "idle" ? "Start listening" : "Listening in progress"}
      >
        {/* Pulsing rings - sirf "listening" state mein dikhte hain */}
        <span className="ring ring--outer" aria-hidden="true"></span>
        <span className="ring ring--middle" aria-hidden="true"></span>
        <span className="ring ring--inner" aria-hidden="true"></span>

        <span className="listen-button__core">
          <MicIcon />
        </span>
      </button>

      <p className="listen-status">
        {status === "idle" && "Tap to identify a song"}
        {status === "listening" && "Listening..."}
        {status === "identifying" && "Identifying..."}
        {status === "result" && result?.match && "Match found"}
        {status === "result" && !result?.match && "Not recognized"}
      </p>

      {errorMessage && <p className="listen-error">{errorMessage}</p>}

      {status === "result" && result && (
        <div className="result-card">
          {result.match ? (
            <>
              <p className="result-title">{result.title}</p>
              <p className="result-artist">{result.artist}</p>
              <p className="result-confidence">confidence: {result.confidence}</p>
            </>
          ) : (
            <p className="result-artist">
              Is clip ka koi match database mein nahi mila.
            </p>
          )}
          <button className="result-reset" onClick={handleReset}>
            Try again
          </button>
        </div>
      )}
    </div>
  );
}

function MicIcon() {
  return (
    <svg width="34" height="34" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 15a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3Z"
        stroke="currentColor"
        strokeWidth="1.8"
      />
      <path
        d="M19 11a7 7 0 0 1-14 0M12 18v3"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default ListenButton;