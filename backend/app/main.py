from fastapi import FastAPI

app = FastAPI(title='NL to SQL Analytics Assistant')

@app.get('/')
def root():
    return {'status': 'ok'}

