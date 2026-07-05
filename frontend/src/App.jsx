import { useState, useEffect, useCallback } from "react";
import Header from "./components/Header";
import ListenButton from "./components/ListenButton";
import AddSongForm from "./components/AddSongForm";
import "./App.css";

const BACKEND_URL = "http://localhost:5000";

function App() {
  // Song counter ka data yahan (parent mein) rakha hai, taake
  // Header aur AddSongForm dono isay share kar sakein - jab
  // AddSongForm mein song add ho, Header ka counter turant update ho.
  const [songCount, setSongCount] = useState(0);
  const [maxSongs, setMaxSongs] = useState(1000);

  const refreshCount = useCallback(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/songs/count`);
      const data = await response.json();
      setSongCount(data.count);
      setMaxSongs(data.max);
    } catch (error) {
      // Backend abhi chal nahi raha - chup-chaap ignore karte hain,
      // counter bas 0 dikhata rahega jab tak backend start na ho
      console.warn("Songs count fetch nahi ho saka:", error);
    }
  }, []);

  // App khulte hi ek baar counter fetch karo
  useEffect(() => {
    refreshCount();
  }, [refreshCount]);

  return (
    <div className="app-shell">
      <Header songCount={songCount} maxSongs={maxSongs} />

      <main className="app-main">
        <ListenButton />
        <AddSongForm onSongAdded={refreshCount} />
      </main>
    </div>
  );
}

export default App;