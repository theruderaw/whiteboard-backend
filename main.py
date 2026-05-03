from fastapi import FastAPI


app = FastAPI()

@app.get("/")
def hello():
    return {"data":"hello_world"}