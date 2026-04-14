/**
 * Manages microphone recording, WAV conversion, and backend upload.
 */

import { useCallback, useRef } from "react"

import { uploadVoiceRecording } from "../services/api"
import styles from "./VoiceRecorder.module.css"

const PREFERRED_MIME_TYPES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/ogg;codecs=opus",
  "audio/ogg",
  "audio/mp4",
]

function getSupportedMimeType() {
  return PREFERRED_MIME_TYPES.find((type) => MediaRecorder.isTypeSupported(type)) || ""
}

export default function VoiceRecorder({
  recordingState,
  setRecordingState,
  setAudioStream,
  onResult,
  onError,
}) {
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  const uploadAudio = useCallback(
    async (blob) => {
      try {
        const wavBlob = await convertBlobToWav(blob)
        const wavFile = new File([wavBlob], "recording.wav", {
          type: "audio/wav",
        })
        const data = await uploadVoiceRecording(wavFile)
        onResult(data)
      } catch (err) {
        onError(`Pipeline failed: ${err.message}`)
      } finally {
        setRecordingState("idle")
      }
    },
    [onError, onResult, setRecordingState]
  )

  const startRecording = useCallback(async () => {
    chunksRef.current = []

    let stream
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
        },
      })
    } catch {
      onError("Microphone access denied. Please allow microphone permissions.")
      return
    }

    setAudioStream(stream)

    const mimeType = getSupportedMimeType()
    const options = mimeType ? { mimeType } : {}

    let recorder
    try {
      recorder = new MediaRecorder(stream, options)
    } catch (err) {
      stream.getTracks().forEach((track) => track.stop())
      setAudioStream(null)
      onError(`Failed to create MediaRecorder: ${err.message}`)
      return
    }

    recorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        chunksRef.current.push(event.data)
      }
    }

    recorder.onerror = (event) => {
      stream.getTracks().forEach((track) => track.stop())
      setAudioStream(null)
      onError(`Recording error: ${event.error?.message || "Unknown error"}`)
      setRecordingState("idle")
    }

    recorder.onstop = async () => {
      stream.getTracks().forEach((track) => track.stop())
      setAudioStream(null)

      const blob = new Blob(chunksRef.current, {
        type: mimeType || "audio/webm",
      })
      chunksRef.current = []

      if (blob.size < 1000) {
        onError("Recording too short. Please speak for at least 1 second.")
        setRecordingState("idle")
        return
      }

      await uploadAudio(blob)
    }

    mediaRecorderRef.current = recorder
    recorder.start(250)
    setRecordingState("recording")
  }, [onError, setAudioStream, setRecordingState, uploadAudio])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop()
      setRecordingState("processing")
    }
  }, [setRecordingState])

  const handleClick = () => {
    if (recordingState === "idle") {
      startRecording()
      return
    }

    if (recordingState === "recording") {
      stopRecording()
    }
  }

  return (
    <div className={styles.wrapper}>
      <button
        className={styles.micButton}
        data-state={recordingState}
        onClick={handleClick}
        disabled={recordingState === "processing"}
        aria-label={recordingState === "recording" ? "Stop recording" : "Start recording"}
        title={recordingState === "recording" ? "Tap to stop" : "Tap to speak"}
      >
        {recordingState === "recording" && (
          <>
            <span className={styles.ring1} aria-hidden="true" />
            <span className={styles.ring2} aria-hidden="true" />
          </>
        )}

        <span className={styles.icon} aria-hidden="true">
          {recordingState === "idle" && <MicIcon />}
          {recordingState === "recording" && <StopIcon />}
          {recordingState === "processing" && <SpinnerIcon />}
        </span>
      </button>

      <div className={styles.hint}>
        {recordingState === "idle" && "Tap to speak"}
        {recordingState === "recording" && "Tap to stop - I'm listening..."}
        {recordingState === "processing" && "Transcribing and thinking..."}
      </div>
    </div>
  )
}

async function convertBlobToWav(blob) {
  const AudioContextCtor = window.AudioContext || window.webkitAudioContext
  if (!AudioContextCtor) {
    throw new Error("This browser does not support Web Audio.")
  }

  const arrayBuffer = await blob.arrayBuffer()
  const audioContext = new AudioContextCtor()

  try {
    const decoded = await audioContext.decodeAudioData(arrayBuffer.slice(0))
    const monoSamples = await resampleToMono16k(decoded)
    return encodeWav(monoSamples)
  } finally {
    await audioContext.close()
  }
}

async function resampleToMono16k(audioBuffer) {
  const targetRate = 16000
  const frameCount = Math.max(1, Math.ceil(audioBuffer.duration * targetRate))
  const OfflineAudioContextCtor =
    window.OfflineAudioContext || window.webkitOfflineAudioContext

  if (!OfflineAudioContextCtor) {
    throw new Error("This browser does not support offline audio rendering.")
  }

  const offlineContext = new OfflineAudioContextCtor(1, frameCount, targetRate)
  const source = offlineContext.createBufferSource()
  const monoBuffer = offlineContext.createBuffer(
    1,
    audioBuffer.length,
    audioBuffer.sampleRate
  )

  const monoChannel = monoBuffer.getChannelData(0)
  for (let channel = 0; channel < audioBuffer.numberOfChannels; channel += 1) {
    const channelData = audioBuffer.getChannelData(channel)
    for (let index = 0; index < channelData.length; index += 1) {
      monoChannel[index] += channelData[index] / audioBuffer.numberOfChannels
    }
  }

  source.buffer = monoBuffer
  source.connect(offlineContext.destination)
  source.start(0)

  const rendered = await offlineContext.startRendering()
  return rendered.getChannelData(0)
}

function encodeWav(channelData) {
  const bytesPerSample = 2
  const sampleRate = 16000
  const dataSize = channelData.length * bytesPerSample
  const buffer = new ArrayBuffer(44 + dataSize)
  const view = new DataView(buffer)

  writeString(view, 0, "RIFF")
  view.setUint32(4, 36 + dataSize, true)
  writeString(view, 8, "WAVE")
  writeString(view, 12, "fmt ")
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * bytesPerSample, true)
  view.setUint16(32, bytesPerSample, true)
  view.setUint16(34, 16, true)
  writeString(view, 36, "data")
  view.setUint32(40, dataSize, true)

  let offset = 44
  for (let index = 0; index < channelData.length; index += 1) {
    const sample = Math.max(-1, Math.min(1, channelData[index]))
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true)
    offset += bytesPerSample
  }

  return new Blob([buffer], { type: "audio/wav" })
}

function writeString(view, offset, value) {
  for (let index = 0; index < value.length; index += 1) {
    view.setUint8(offset + index, value.charCodeAt(index))
  }
}

function MicIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="2" width="6" height="11" rx="3" />
      <path d="M5 10a7 7 0 0 0 14 0" />
      <line x1="12" y1="19" x2="12" y2="22" />
      <line x1="8" y1="22" x2="16" y2="22" />
    </svg>
  )
}

function StopIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
      <rect x="6" y="6" width="12" height="12" rx="2" />
    </svg>
  )
}

function SpinnerIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83">
        <animateTransform attributeName="transform" type="rotate" values="0 12 12;360 12 12" dur="1s" repeatCount="indefinite" />
      </path>
    </svg>
  )
}
