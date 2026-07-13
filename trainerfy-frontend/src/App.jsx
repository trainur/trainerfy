import { useState } from "react";
import { FaGithub } from "react-icons/fa"
import "./App.css"; 

class SongResult {
  constructor(title, artist, album = null, artwork = null, artwork_mime = null) {
    this.title = title;
    this.artist = artist;
    this.album = album;
    this.artwork = artwork;
    this.artwork_mime = artwork_mime;
  }
}

export default function App() {
  const [listening, setListening] = useState(false);
  const [result, setResult] = useState(null);
  const [identifying, setIdentifying] = useState(false);
  const [noResult, setNoResult] = useState(false);
  const [searchExit, setSearchExit] = useState(false);

  async function startListening() {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: false,
        noiseSuppression: false,
        autoGainControl: false,
        channelCount: 1,
        sampleRate: 44100
      }
    });

    const mediaRecorder = new MediaRecorder(stream, {
      mimeType: "audio/webm;codecs=opus"
    });

    const chunks = [];

    return new Promise((resolve) => {
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunks, {
          type: mediaRecorder.mimeType
        });

        stream.getTracks().forEach((track) => track.stop());
        resolve(audioBlob);
      };

      mediaRecorder.start(1000);

      setTimeout(() => {
        mediaRecorder.stop();
      }, 15000);
    });
  }

  async function handleListen() {
    setListening(true);
    setIdentifying(false);
    setResult(null);
    setNoResult(false);
    setSearchExit(false);

    const audio_file = await startListening();

    setListening(false)
    setIdentifying(true)

    const response = await fetch("http://localhost:5000/identify", {method: "POST", body: audio_file});
    const data = await response.json();

    setSearchExit(true);
    await new Promise((resolve) => setTimeout(resolve, 350));
    
    setIdentifying(false)
    setListening(false);

    if (data.success) {
      setResult(new SongResult(data.title, data.artist, data.album, data.artwork, data.artwork_mime));
    } else {
      setNoResult(true);
    }
  }
 
  function handleReset() {
    setListening(false);
    setResult(null);
  }
 
  return (
  <div className="app">
    <div className="top-section">
      <h1 className="title">trainerfy</h1>
      <br/>

      <button 
        className="listen-button"
        onClick={handleListen} 
        disabled={listening || identifying}
      >
        Identify Song
      </button>
    </div>
  

    <div className="result-slot">
      {listening && (
        <div className="status-area">
          <div className="pulse-ring">
            <div className="wave-bars">
              {Array.from({ length: 5 }).map((_, i) =>  <span key={i}/>)}
            </div>
          </div>
        </div>
      )}

      {identifying && (
        <div className={`status-area ${searchExit ? "search-exit" : ""}`}>
          <div className="search-icon">
            <div className="magnifier">
              <div className="glass"/>
              <div className="handle"/>
              <div className="scan-line-move">
                <div className="scan-line-scale"></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {result && (
        <div className="result-card">
          {result.artwork && (
            <img
              className="result-bg-artwork"
              src={`data:${result.artwork_mime || "image/jpeg"};base64,${result.artwork}`}
              alt=""
            />
          )}

          <div className="result-content">
            {result.artwork && (
              <img
                className="artwork"
                src={`data:${result.artwork_mime || "image/jpeg"};base64,${result.artwork}`}
                alt={`${result.title} artwork`}
              />
            )}

            <p><strong>Title:</strong> {result.title}</p>
            <p><strong>Artist:</strong> {result.artist}</p>
            {result.album && <p><strong>Album:</strong> {result.album}</p>}
          </div>
        </div>
      )}

      {noResult && (
        <div className="no-result-card">
          <div className="no-result-icon">?</div>
          <h2>No song found</h2>
          <p>Try again with a clearer or louder sound sample</p>
        </div>
      )}
    </div>

    <a
    className="github-link"
    href="https://github.com/trainur"
    target="_blank"
    rel="noopener noreferrer"
    aria-label="My Github"
  >
      <FaGithub className="github-icon"/>
  </a>
  </div>
);
}