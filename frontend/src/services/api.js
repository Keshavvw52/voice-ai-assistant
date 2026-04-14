import { getStoredToken } from "./auth"

const API_HEADERS = {
  Accept: "application/json",
}

async function apiFetch(path, options = {}) {
  const token = getStoredToken()

  const response = await fetch(path, {
    ...options,
    headers: {
      ...API_HEADERS,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  })

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw new Error(payload.detail || `HTTP ${response.status}`)
  }

  const contentType = response.headers.get("content-type") || ""
  if (contentType.includes("application/json")) {
    return response.json()
  }

  return response.text()
}

export async function uploadVoiceRecording(file) {
  const formData = new FormData()
  formData.append("file", file, file.name)
  return apiFetch("/api/voice/upload", {
    method: "POST",
    body: formData,
  })
}

export async function fetchTasks() {
  return apiFetch("/api/tasks")
}

export async function updateTaskStatus(taskId, status) {
  return apiFetch(`/api/tasks/${taskId}/status`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ status }),
  })
}

export async function deleteTask(taskId) {
  return apiFetch(`/api/tasks/${taskId}`, {
    method: "DELETE",
  })
}
