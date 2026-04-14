/**
 * WaveformVisualizer.jsx
 * Renders a real-time animated waveform from a MediaStream using
 * the Web Audio API and a Canvas element.
 */

import { useEffect, useRef } from 'react'
import styles from './WaveformVisualizer.module.css'

const BAR_COUNT  = 48
const BAR_GAP    = 3
const MIN_HEIGHT = 3
const ACCENT     = 'rgba(0, 229, 255, '

export default function WaveformVisualizer({ stream, isActive }) {
  const canvasRef        = useRef(null)
  const animFrameRef     = useRef(null)
  const analyserRef      = useRef(null)
  const audioCtxRef      = useRef(null)
  const sourceRef        = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    if (!isActive || !stream) {
      // Draw idle flat line
      drawIdle(ctx, canvas)
      return
    }

    // Build audio graph: stream → analyser → (no destination, just read data)
    const AudioContext = window.AudioContext || window.webkitAudioContext
    if (!AudioContext) return

    const audioCtx = new AudioContext()
    const analyser  = audioCtx.createAnalyser()
    analyser.fftSize           = 128
    analyser.smoothingTimeConstant = 0.8

    const source = audioCtx.createMediaStreamSource(stream)
    source.connect(analyser)

    audioCtxRef.current = audioCtx
    analyserRef.current = analyser
    sourceRef.current   = source

    const dataArray = new Uint8Array(analyser.frequencyBinCount)

    const draw = () => {
      animFrameRef.current = requestAnimationFrame(draw)
      analyser.getByteFrequencyData(dataArray)

      // Resize canvas to match display size
      const { width, height } = canvas.getBoundingClientRect()
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width  = width
        canvas.height = height
      }

      ctx.clearRect(0, 0, width, height)

      const barWidth   = (width - BAR_GAP * (BAR_COUNT - 1)) / BAR_COUNT
      const binStep    = Math.floor(dataArray.length / BAR_COUNT)

      for (let i = 0; i < BAR_COUNT; i++) {
        // Average a few bins per bar for smoother output
        const binStart = i * binStep
        let   sum      = 0
        for (let b = binStart; b < binStart + binStep; b++) {
          sum += dataArray[b] || 0
        }
        const avg      = sum / binStep
        const norm     = avg / 255            // 0–1
        const barH     = Math.max(MIN_HEIGHT, norm * height * 0.9)

        const x = i * (barWidth + BAR_GAP)
        const y = (height - barH) / 2

        // Gradient bar: brighter in center
        const alpha  = 0.35 + norm * 0.65
        const grd    = ctx.createLinearGradient(x, y, x, y + barH)
        grd.addColorStop(0,   `${ACCENT}${alpha * 0.4})`)
        grd.addColorStop(0.5, `${ACCENT}${alpha})`)
        grd.addColorStop(1,   `${ACCENT}${alpha * 0.4})`)

        ctx.fillStyle   = grd
        ctx.beginPath()
        ctx.roundRect(x, y, barWidth, barH, barWidth / 2)
        ctx.fill()
      }
    }

    draw()

    return () => {
      cancelAnimationFrame(animFrameRef.current)
      source.disconnect()
      audioCtx.close()
    }
  }, [stream, isActive])

  return (
    <div className={styles.wrapper} aria-hidden="true">
      <canvas ref={canvasRef} className={styles.canvas} />
    </div>
  )
}

/** Draw a subtle flat idle line */
function drawIdle(ctx, canvas) {
  const { width, height } = canvas.getBoundingClientRect()
  canvas.width  = width  || 300
  canvas.height = height || 60

  ctx.clearRect(0, 0, canvas.width, canvas.height)

  const barWidth = (canvas.width - BAR_GAP * (BAR_COUNT - 1)) / BAR_COUNT

  for (let i = 0; i < BAR_COUNT; i++) {
    const x = i * (barWidth + BAR_GAP)
    const y = (canvas.height - MIN_HEIGHT) / 2
    ctx.fillStyle = 'rgba(0, 229, 255, 0.12)'
    ctx.beginPath()
    ctx.roundRect(x, y, barWidth, MIN_HEIGHT, MIN_HEIGHT / 2)
    ctx.fill()
  }
}