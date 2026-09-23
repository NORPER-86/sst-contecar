with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Completely remove the 'Escanear Carpeta Completa' radio option so it defaults to Drag & Drop
old_radio = '["📁 Escanear Carpeta Completa (Batch)", "🗂️ Arrastrar Múltiples Archivos (Drag & Drop)", "🔍 Seleccionar Archivo Individual"]'
new_radio = '["🗂️ Arrastrar Múltiples Archivos (Drag & Drop)", "🔍 Seleccionar Archivo Individual"]'
content = content.replace(old_radio, new_radio)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
