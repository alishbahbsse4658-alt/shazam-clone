/*
  Header.jsx
  ----------
  Top bar: app ka logo/naam (left) aur live song counter pill (right).
  Counter ka data App.jsx se aata hai (prop ke zariye), taake jab
  bhi koi naya song add ho, poori app mein counter turant update ho jaye.
*/

import "./Header.css";

function Header({ songCount, maxSongs }) {
  return (
    <header className="app-header">
      <h1 className="app-logo">
        <span className="app-logo__mark">!</span>Shazam_Clone
      </h1>

      <div className="song-counter" role="status" aria-live="polite">
        <span className="song-counter__count">{songCount}</span>
        <span className="song-counter__divider">/</span>
        <span className="song-counter__max">{maxSongs} songs</span>
      </div>
    </header>
  );
}

export default Header;