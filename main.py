from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlmodel import Field, Session, SQLModel, create_engine, select
from datetime import datetime
from typing import Optional, List
import uvicorn

# --- 数据库配置 ---
sqlite_file_name = "/data/database.db" # 数据存储在挂载卷中
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

class Record(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    result: str  # "win" 或 "loss"
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# --- App 初始化 ---
app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- API 接口 ---

# 1. 获取主页
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 2. 获取所有记录
@app.get("/api/records", response_model=List[Record])
def read_records():
    with Session(engine) as session:
        # 按时间倒序排列
        statement = select(Record).order_by(Record.created_at.desc())
        results = session.exec(statement).all()
        return results

# 3. 添加记录
@app.post("/api/records", response_model=Record)
def create_record(record: Record):
    with Session(engine) as session:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

# 4. 删除记录
@app.delete("/api/records/{record_id}")
def delete_record(record_id: int):
    with Session(engine) as session:
        record = session.get(Record, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        session.delete(record)
        session.commit()
        return {"ok": True}

# 5. 更新记录 (可选)
@app.put("/api/records/{record_id}")
def update_record(record_id: int, data: Record):
    with Session(engine) as session:
        record = session.get(Record, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        record.result = data.result
        record.note = data.note
        record.created_at = data.created_at
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)