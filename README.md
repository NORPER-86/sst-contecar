# SST ComPORTate - SURA & Grupo Puerto de Cartagena (CONTECAR / SPRC)

Sistema de Digitalización Inteligente, Extracción Multimodal y Calificación Automatizada de Observaciones de Seguridad Basada en Comportamientos (SBC).

---

## 🚀 Acceso en Producción
* **URL de la Aplicación en Vivo:** [https://sst-contecar-uddimimtns7w5nzav82a9f.streamlit.app/](https://sst-contecar-uddimimtns7w5nzav82a9f.streamlit.app/)

---

## 📖 Documentación Técnica Completa
Para una explicación exhaustiva de la arquitectura, alcance, logros alcanzados, frustraciones técnicas y el catálogo completo de errores presentados (resueltos y pendientes), consulta el documento maestro:
👉 **[Docs/MEMORIA_TECNICA_Y_ESTADO_DEL_PROYECTO.md](Docs/MEMORIA_TECNICA_Y_ESTADO_DEL_PROYECTO.md)**

---

## 🛠️ Ejecución Local y Desarrollo

### 1. Clonar el repositorio
```bash
git clone https://github.com/NORPER-86/sst-contecar.git
cd sst-contecar
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación
```bash
streamlit run app.py
```

---

## 🧪 Pruebas Automatizadas (Quality Gate)
El proyecto cuenta con una suite de 19 pruebas unitarias y de humo que validan el motor de scoring, la extracción y el AST de `app.py`:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 🛡️ Gobernanza con OpenSpec (Spec-Driven Development)
Las especificaciones formales del proyecto se gestionan con `@fission-ai/openspec`:
* `openspec/specs/observation-engine/spec.md`: Reglas del motor matemático de scoring SURA y mapeo de 44 columnas.
* `openspec/specs/app-stability-guard/spec.md`: Guardián de estabilidad y análisis de AST pre-despliegue.

Para validar el estado de las especificaciones:
```bash
openspec validate
```
