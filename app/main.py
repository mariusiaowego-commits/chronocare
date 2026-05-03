from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="ChronoCare", description="老年父母健康管理平台")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板引擎
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def root():
    return {"message": "Welcome to ChronoCare"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}