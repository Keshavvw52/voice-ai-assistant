import { useCallback, useEffect, useState } from "react";

import Login from "./pages/Login"; //

import bgImage from "./assets/bg.jpg";

import VoiceRecorder from "./components/VoiceRecorder";
import WaveformVisualizer from "./components/WaveformVisualizer";
import LiveTranscript from "./components/LiveTranscript";
import TaskList from "./components/TaskList";
import AudioPlayer from "./components/AudioPlayer";
import { clearToken, getStoredToken, isTokenValid } from "./services/auth";

import styles from "./App.module.css";

export default function App() {
  // 🔐 Auth state
  const [isLoggedIn, setIsLoggedIn] = useState(() =>
    isTokenValid(getStoredToken())
  );

  // 🎤 App states
  const [recordingState, setRecordingState] = useState("idle");
  const [audioStream, setAudioStream] = useState(null);
  const [transcript, setTranscript] = useState("");
  const [intentLabel, setIntentLabel] = useState("");
  const [responseText, setResponseText] = useState("");
  const [audioUrl, setAudioUrl] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = getStoredToken();

    if (!isTokenValid(token)) {
      clearToken();
      setIsLoggedIn(false);
    }
  }, []);

  // 🎯 Handle AI result
  const handleResult = useCallback((result) => {
    setTranscript(result.transcript || "");
    setIntentLabel(result.intent || "");
    setResponseText(result.response_text || "");
    setAudioUrl(result.audio_url || null);
    setTasks(result.tasks || []);
    setError(null);
  }, []);

  // ⚠ Handle error
  const handleError = useCallback((msg) => {
    setError(msg);
    setRecordingState("idle");
  }, []);

  // 🔐 Show login if not authenticated
  if (!isLoggedIn) {
    return <Login onLogin={() => setIsLoggedIn(true)} />;
  }

  // 🚪 Logout function
  const handleLogout = () => {
    clearToken();
    setRecordingState("idle");
    setAudioStream(null);
    setTranscript("");
    setIntentLabel("");
    setResponseText("");
    setAudioUrl(null);
    setTasks([]);
    setError(null);
    setIsLoggedIn(false);
  };

  return (
    <div
      className={styles.root}
      style={{ backgroundImage: `url(${bgImage})` }}
    >
      <div className={styles.overlay}></div>
      <div className={styles.noise}></div>

      <div className={styles.layout}>
        {/* LEFT SIDE */}
        <div className={styles.left}>
          <header className={styles.hero}>
            <div className={styles.kicker}>Voice Desk</div>

            <h1 className={styles.title}>MAX</h1>

            <p className={styles.subtitle}>
              A focused voice assistant for quick capture, clean replies, and a
              task board that stays out of your way.
            </p>

            {/* 🔴 Logout Button */}
           <button onClick={handleLogout} className={styles.logoutBtn}>
  Logout
</button>
          </header>

          <div className={styles.card}>
            <WaveformVisualizer
              stream={audioStream}
              isActive={recordingState === "recording"}
            />

            <VoiceRecorder
              recordingState={recordingState}
              setRecordingState={setRecordingState}
              setAudioStream={setAudioStream}
              onResult={handleResult}
              onError={handleError}
            />

            {error && <div className={styles.error}>⚠ {error}</div>}

            <LiveTranscript
              transcript={transcript}
              intent={intentLabel}
              responseText={responseText}
              isProcessing={recordingState === "processing"}
            />

            {audioUrl && <AudioPlayer audioUrl={audioUrl} autoPlay />}
          </div>
        </div>

        {/* RIGHT SIDE */}
        <div className={styles.right}>
          <div className={styles.taskCard}>
            <div className={styles.taskHeading}>Tasks</div>
            <TaskList tasks={tasks} onTasksChange={setTasks} />
          </div>
        </div>
      </div>
    </div>
  );
}
