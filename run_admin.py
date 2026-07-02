
import uvicorn
from admin.main import app

if __name__ == "__main__":
    # host=0.0.0.0 — чтобы порт можно было пробросить наружу (например, через
    # port forwarding в VS Code / devtunnels) для тестирования извне.
    uvicorn.run("admin.main:app", host="0.0.0.0", port=8000, reload=True)