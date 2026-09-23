with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

insert_idx = 0
for i, line in enumerate(lines):
    if '# TAB 3: BASE DE DATOS MAESTRA (44 COLUMNAS)' in line:
        insert_idx = i - 1
        break

code_to_insert = """
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("#### 📝 Generador de Informe Ejecutivo Automático")
            st.caption("Genera un resumen en texto clasificado por las categorías de calidad A, B, C, D basado en tus filtros.")
            
            if st.button("Generar Informe de la Selección", type="secondary"):
                with st.spinner("La Inteligencia Artificial está redactando el informe ejecutivo..."):
                    try:
                        from google import genai
                        client = genai.Client()
                        
                        resumen_cat = df_filtered["categoria"].value_counts().to_dict()
                        total_obs = len(df_filtered)
                        
                        prompt = f'''
Eres el Director de Seguridad y Salud en el Trabajo (SST) de CONTECAR / SURA.
Acabas de revisar un lote de {total_obs} observaciones de comportamiento.
La distribución de calidad de las observaciones es la siguiente (Matriz SURA):
{resumen_cat}

Contexto de calificaciones:
- A / A+: Sobresalientes, alto impacto.
- B / B+: Buenas, planes de mejora estándar.
- C / C+: Regulares, incompletas pero funcionales.
- D: Deficientes, requieren subsanación.

Escribe un reporte ejecutivo formal y corto (máximo 3 párrafos).
1. Un párrafo resumiendo el balance general.
2. Un desglose en viñetas (bullet points) destacando las clasificaciones.
3. Una recomendación final para los supervisores.
'''
                        
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt
                        )
                        st.success("Informe generado con éxito:")
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"No se pudo generar el informe: {e}")
"""

lines.insert(insert_idx, code_to_insert)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
