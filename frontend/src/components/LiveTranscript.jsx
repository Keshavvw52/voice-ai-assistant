/**
 * LiveTranscript.jsx
 * Displays the transcribed user speech, detected intent badge,
 * and the AI's natural-language response.
 */

import styles from './LiveTranscript.module.css'

const INTENT_LABELS = {
  create_task:  { label: 'Create Task',  color: '#39d98a' },
  list_tasks:   { label: 'List Tasks',   color: '#00e5ff' },
  delete_task:  { label: 'Delete Task',  color: '#ff4d6d' },
  small_talk:   { label: 'Small Talk',   color: '#ffd166' },
  unknown:      { label: 'Unknown',      color: '#888'    },
}

export default function LiveTranscript({
  transcript,
  intent,
  responseText,
  isProcessing,
}) {
  const intentMeta = INTENT_LABELS[intent] || null

  if (isProcessing) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.processingRow}>
          <div className={styles.dots}>
            <span /><span /><span />
          </div>
          <span className={styles.processingLabel}>Analysing your request…</span>
        </div>
      </div>
    )
  }

  if (!transcript && !responseText) {
    return (
      <div className={styles.wrapper}>
        <p className={styles.placeholder}>
          Your speech will appear here after recording…
        </p>
      </div>
    )
  }

  return (
    <div className={styles.wrapper}>
      {/* ── User speech row ── */}
      {transcript && (
        <div className={styles.block} style={{ animationDelay: '0ms' }}>
          <div className={styles.blockHeader}>
            <span className={styles.roleTag} data-role="user">You</span>
            {intentMeta && (
              <span
                className={styles.intentBadge}
                style={{ color: intentMeta.color, borderColor: `${intentMeta.color}44` }}
              >
                {intentMeta.label}
              </span>
            )}
          </div>
          <p className={styles.text}>{transcript}</p>
        </div>
      )}

      {/* ── AI response row ── */}
      {responseText && (
        <div className={styles.block} style={{ animationDelay: '80ms' }}>
          <div className={styles.blockHeader}>
            <span className={styles.roleTag} data-role="ai">MAX</span>
          </div>
          <p className={styles.text}>{responseText}</p>
        </div>
      )}
    </div>
  )
}
