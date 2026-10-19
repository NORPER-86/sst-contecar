"""
Punto de entrada compatible con Streamlit Community Cloud.
Redirige y ejecuta el núcleo oficial de app.py de manera transparente.
"""
import runpy

if __name__ == "__main__":
    runpy.run_path("app.py", run_name="__main__")
