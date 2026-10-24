from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = create_async_engine("sqlite+aiosqlite:///tasks.db")

new_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_session() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

class Base(DeclarativeBase):
    pass

class TaskAddModel(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    is_done: Mapped[bool] = mapped_column(default=False)

class TaskAdd(BaseModel):
    title: str
    description: str

class Task(TaskAdd):
    id: int
    is_done: bool = False

class TaskUpdate(BaseModel):
    is_done: bool

@app.post("/setup_database")
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return {"ok":True, "msg": "Таблицы созданы"}


@app.post("/tasks")
async def create_task(task: TaskAdd, session: SessionDep):
    new_task = TaskAddModel(
        title = task.title,
        description = task.description
    )
    session.add(new_task)
    await session.commit()
    return {"ok":True, "msg":"Задача успешно добавлена"}

@app.get("/tasks")
async def get_tasks(session: SessionDep):
    qweru = select(TaskAddModel)
    res = await session.execute(qweru)
    return res.scalars().all()

@app.patch("/tasks/{task_id}")
async def patch_in_task(task_id: int, session:SessionDep, data:TaskUpdate):
    task = await session.get(TaskAddModel, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    task.is_done = data.is_done
    await session.commit()
    return {"ok":True, "msg":f"Статус задачи {task_id} изменён на {data.is_done}"}


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, session:SessionDep):
    task = await session.get(TaskAddModel, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    await session.delete(task)
    await session.commit()
    return {"ok":True, "msg":f"Задача под номером {task_id} успешно удалена"}