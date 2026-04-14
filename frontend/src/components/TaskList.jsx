/**
 * Displays and manages tasks returned by the backend.
 */

import { useCallback, useEffect, useState } from "react"

import {
  deleteTask as deleteTaskRequest,
  fetchTasks as fetchTasksRequest,
  updateTaskStatus,
} from "../services/api"
import styles from "./TaskList.module.css"

export default function TaskList({ tasks, onTasksChange }) {
  const [localTasks, setLocalTasks] = useState(tasks || [])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLocalTasks(tasks || [])
  }, [tasks])

  const fetchTasks = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchTasksRequest()
      setLocalTasks(data)
      onTasksChange?.(data)
    } catch {
      setError("Failed to load tasks")
    } finally {
      setLoading(false)
    }
  }, [onTasksChange])

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  const toggleComplete = async (task) => {
    const newStatus = task.status === "completed" ? "pending" : "completed"
    try {
      const updated = await updateTaskStatus(task.id, newStatus)
      setLocalTasks((prev) => {
        const next = prev.map((item) => (item.id === task.id ? updated : item))
        onTasksChange?.(next)
        return next
      })
    } catch {
      setError("Failed to update task")
    }
  }

  const deleteTask = async (taskId) => {
    try {
      await deleteTaskRequest(taskId)
      setLocalTasks((prev) => {
        const next = prev.filter((task) => task.id !== taskId)
        onTasksChange?.(next)
        return next
      })
    } catch {
      setError("Failed to delete task")
    }
  }

  const pendingTasks = localTasks.filter((task) => task.status !== "completed")
  const completedTasks = localTasks.filter((task) => task.status === "completed")

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span className={styles.title}>Task Board</span>
        <span className={styles.count}>{pendingTasks.length}</span>
        <button
          className={styles.refreshBtn}
          onClick={fetchTasks}
          disabled={loading}
          title="Refresh tasks"
          aria-label="Refresh tasks"
        >
          <RefreshIcon spinning={loading} />
        </button>
      </div>

      {error && <div className={styles.error}>⚠ {error}</div>}

      {!loading && localTasks.length === 0 && (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>◻</div>
          <p>No tasks yet</p>
          <p>Try saying "Add task buy groceries"</p>
        </div>
      )}

      {pendingTasks.length > 0 && (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>Pending</div>
          <ul className={styles.list}>
            {pendingTasks.map((task, index) => (
              <TaskItem
                key={task.id}
                task={task}
                index={index}
                onToggle={toggleComplete}
                onDelete={deleteTask}
              />
            ))}
          </ul>
        </div>
      )}

      {completedTasks.length > 0 && (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>Done</div>
          <ul className={styles.list}>
            {completedTasks.map((task, index) => (
              <TaskItem
                key={task.id}
                task={task}
                index={index}
                onToggle={toggleComplete}
                onDelete={deleteTask}
              />
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function TaskItem({ task, index, onToggle, onDelete }) {
  const isDone = task.status === "completed"

  return (
    <li
      className={styles.item}
      data-done={isDone}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <button
        className={styles.check}
        onClick={() => onToggle(task)}
        aria-label={isDone ? "Mark incomplete" : "Mark complete"}
        data-done={isDone}
      >
        {isDone && <CheckIcon />}
      </button>

      <div className={styles.itemContent}>
        <span className={styles.itemTitle}>{task.title}</span>
        {task.due_date && <span className={styles.dueDate}>⏱ {task.due_date}</span>}
      </div>

      <button
        className={styles.deleteBtn}
        onClick={() => onDelete(task.id)}
        aria-label={`Delete task: ${task.title}`}
        title="Delete"
      >
        ×
      </button>
    </li>
  )
}

function CheckIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="1.5,5 4,7.5 8.5,2" />
    </svg>
  )
}

function RefreshIcon({ spinning }) {
  return (
    <svg
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{ animation: spinning ? "spin 0.8s linear infinite" : "none" }}
    >
      <polyline points="23 4 23 10 17 10" />
      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
    </svg>
  )
}
