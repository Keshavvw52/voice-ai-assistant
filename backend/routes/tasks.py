"""
Task Management API Routes — full CRUD via HTTP.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from services import task_service
from services.auth_service import get_current_user
from models.schemas import TaskCreate, TaskUpdate, TaskResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=list[TaskResponse])
async def get_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user=Depends(get_current_user),
):
    """List all tasks, optionally filtered by status."""
    tasks = await task_service.list_tasks(current_user["id"], status)
    return tasks


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(body: TaskCreate, current_user=Depends(get_current_user)):
    """Manually create a new task."""
    task = await task_service.create_task(current_user["id"], body.title, body.due_date)
    return task


@router.delete("/{task_id}", status_code=200)
async def delete_task(task_id: int, current_user=Depends(get_current_user)):
    """Delete a task by ID."""
    deleted = await task_service.delete_task_by_id(current_user["id"], task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return {"message": f"Task {task_id} deleted successfully"}


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: int,
    body: TaskUpdate,
    current_user=Depends(get_current_user),
):
    """Update a task's status (e.g. pending → completed)."""
    if not body.status:
        raise HTTPException(status_code=400, detail="'status' field is required")
    
    task = await task_service.update_task_status(current_user["id"], task_id, body.status)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task
