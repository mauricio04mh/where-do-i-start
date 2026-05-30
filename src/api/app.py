from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.routes import chat, paths, resources, students

app = FastAPI(
    title="Where Do I Start API",
    description="API para gestionar estudiantes, recursos y generar rutas de aprendizaje.",
    version="0.1.0",
)

app.include_router(students.router, prefix="/students", tags=["students"])
app.include_router(resources.router, prefix="/resources", tags=["resources"])
app.include_router(paths.router, prefix="/paths", tags=["paths"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])


@app.get("/")
def read_root() -> dict:
    return {"message": "Where Do I Start API is running"}


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request, exc: RequestValidationError) -> JSONResponse:
    for error in exc.errors():
        location = error.get("loc", ())
        if location[-1:] == ("algorithm",):
            return JSONResponse(status_code=400, content={"detail": exc.errors()})

    return JSONResponse(status_code=422, content={"detail": exc.errors()})
