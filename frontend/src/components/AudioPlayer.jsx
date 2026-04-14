/**
 * AudioPlayer.jsx
 * Plays the TTS-generated audio response automatically.
 * Shows playback controls and progress bar.
 */

import { useEffect, useRef, useState } from 'react'
import styles from './AudioPlayer.module.css'

export default function AudioPlayer({ audioUrl, autoPlay = true }) {
  const audioRef     = useRef(null)
  const [playing, setPlaying]     = useState(false)
  const [progress, setProgress]   = useState(0)
  const [duration, setDuration]   = useState(0)
  const [error, setError]         = useState(null)

  // Auto-play when a new URL arrives
  useEffect(() => {
    if (!audioUrl || !audioRef.current) return

    const audio = audioRef.current

    if (autoPlay) {
      audio.play().catch(() => {
        // Browsers may block autoplay without user gesture
        setError('Click ▶ to play the AI response')
      })
    }
  }, [audioUrl, autoPlay])

  const togglePlay = () => {
    const audio = audioRef.current
    if (!audio) return
    if (playing) audio.pause()
    else         audio.play().catch(() => setError('Playback blocked by browser'))
  }

  const handleTimeUpdate = () => {
    const audio = audioRef.current
    if (!audio) return
    setProgress(audio.currentTime)
    setDuration(audio.duration || 0)
  }

  const handleSeek = (e) => {
    const audio = audioRef.current
    if (!audio || !duration) return
    const rect  = e.currentTarget.getBoundingClientRect()
    const ratio = (e.clientX - rect.left) / rect.width
    audio.currentTime = ratio * duration
  }

  const formatTime = (secs) => {
    if (!secs || isNaN(secs)) return '0:00'
    const m = Math.floor(secs / 60)
    const s = Math.floor(secs % 60).toString().padStart(2, '0')
    return `${m}:${s}`
  }

  const progressPct = duration > 0 ? (progress / duration) * 100 : 0

  if (!audioUrl) return null

  return (
    <div className={styles.player}>
      {/* Hidden native audio element */}
      <audio
        key={audioUrl}
        ref={audioRef}
        src={audioUrl || undefined}
        onLoadStart={() => {
          setError(null)
          setProgress(0)
          setDuration(0)
        }}
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => { setPlaying(false); setProgress(0) }}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleTimeUpdate}
        onError={() => setError('Audio playback error')}
      />

      <div className={styles.inner}>
        {/* Play/pause button */}
        <button
          className={styles.playBtn}
          onClick={togglePlay}
          aria-label={playing ? 'Pause' : 'Play AI response'}
        >
          {playing ? <PauseIcon /> : <PlayIcon />}
        </button>

        {/* Progress bar + label */}
        <div className={styles.right}>
          <div className={styles.label}>
            {error
              ? <span className={styles.errorText}>{error}</span>
              : <span>AI Response</span>
            }
            <span className={styles.time}>
              {formatTime(progress)} / {formatTime(duration)}
            </span>
          </div>

          {/* Clickable scrubber */}
          <div
            className={styles.track}
            onClick={handleSeek}
            role="progressbar"
            aria-valuenow={Math.round(progressPct)}
            aria-valuemin={0}
            aria-valuemax={100}
            title="Click to seek"
          >
            <div
              className={styles.fill}
              style={{ width: `${progressPct}%` }}
            />
            <div
              className={styles.thumb}
              style={{ left: `${progressPct}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function PlayIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <polygon points="5,3 19,12 5,21"/>
    </svg>
  )
}

function PauseIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <rect x="6"  y="4" width="4" height="16" rx="1"/>
      <rect x="14" y="4" width="4" height="16" rx="1"/>
    </svg>
  )
}
