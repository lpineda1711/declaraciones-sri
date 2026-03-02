import streamlit as st
import pandas as pd

st.set_page_config(page_title="Procesador Compras SRI", layout="wide")

st.title("Procesador de Compras - Separado por Mes")

uploaded_files = st.file_uploader(
    "Sube tus archivos TXT",
    type="txt",
    accept_multiple_files=True
)

if uploaded_files:

    dfs = []

    for archivo in uploaded_files:
        try:
            df = pd.read_csv(archivo, sep='\t', encoding='latin1')
            df.columns = df.columns.str.strip()

            df = df.rename(columns={
                "RUC_EMISOR": "RUC",
                "RAZON_SOCIAL_EMISOR": "PROVEEDOR",
                "FECHA_EMISION": "FECHA",
                "VALOR_SIN_IMPUESTOS": "VALOR SIN IMPUESTOS",
                "CLAVE_ACCESO": "Clave de acceso",
                "SERIE_COMPROBANTE": "FACT",
                "IMPORTE_TOTAL": "TOTAL"
            })

            df["IVA"] = pd.to_numeric(df.get("IVA", 0), errors="coerce").fillna(0)
            df["VALOR SIN IMPUESTOS"] = pd.to_numeric(
                df.get("VALOR SIN IMPUESTOS", 0),
                errors="coerce"
            ).fillna(0)

            df["FECHA"] = pd.to_datetime(
                df.get("FECHA"),
                errors="coerce",
                dayfirst=True
            )

            df["BASE 0%"] = df.apply(
                lambda x: x["VALOR SIN IMPUESTOS"] if x["IVA"] == 0 else 0,
                axis=1
            )

            df["BASE 12%"] = df.apply(
                lambda x: x["VALOR SIN IMPUESTOS"] if x["IVA"] != 0 else 0,
                axis=1
            )

            # 🔎 CLASIFICACIÓN AUTOMÁTICA
            def clasificar(proveedor):
                p = str(proveedor).lower()
                if "comida" in p or "restaurant" in p or "super" in p:
                    return "Gastos alimenticios"
                elif "farmacia" in p or "medic" in p or "hospital" in p:
                    return "Médicos"
                elif "gas" in p or "estacion" in p or "petro" in p:
                    return "Combustible"
                else:
                    return "Otros gastos"

            df_limpio = pd.DataFrame()
            df_limpio["FECHA"] = df["FECHA"]
            df_limpio["PROVEEDOR"] = df["PROVEEDOR"]
            df_limpio["RUC"] = df["RUC"]
            df_limpio["FACT"] = df["FACT"]
            df_limpio["Clave de acceso"] = df["Clave de acceso"]
            df_limpio["NO OBJETO"] = ""
            df_limpio["EXCENTO DE IVA"] = ""
            df_limpio["BASE 0%"] = df["BASE 0%"]
            df_limpio["BASE 12%"] = df["BASE 12%"]
            df_limpio["PROPINA"] = 0
            df_limpio["IVA"] = df["IVA"]
            df_limpio["TOTAL"] = df["TOTAL"]
            df_limpio["DESCRIPCIÓN"] = df_limpio["PROVEEDOR"].apply(clasificar)

            df_limpio["ARCHIVO"] = archivo.name.replace(".txt", "")
            dfs.append(df_limpio)

        except Exception as e:
            st.error(f"Error procesando {archivo.name}: {e}")

    if dfs:

        df_final = pd.concat(dfs, ignore_index=True)
        df_final["MES"] = df_final["FECHA"].dt.to_period("M").astype(str)

        st.success("Archivos procesados correctamente")
        st.dataframe(df_final)

        nombre_excel = "compras_formato_profesional.xlsx"

        with pd.ExcelWriter(nombre_excel, engine="xlsxwriter") as writer:

            workbook = writer.book

            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#FFFF00',
                'border': 1,
                'align': 'center'
            })

            left_format = workbook.add_format({
                'border': 1,
                'align': 'left'
            })

            text_format = workbook.add_format({
                'border': 1,
                'align': 'center'
            })

            red_text_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'font_color': 'red'
            })

            date_format = workbook.add_format({
                'border': 1,
                'num_format': 'dd/mm/yyyy',
                'align': 'center'
            })

            number_format = workbook.add_format({
                'border': 1,
                'num_format': '#,##0.00',
                'align': 'center'
            })

            total_format = workbook.add_format({
                'bold': True,
                'bg_color': '#FFFF00',
                'border': 1,
                'num_format': '#,##0.00',
                'align': 'center'
            })

            title_format = workbook.add_format({
                'bold': True,
                'font_size': 16,
                'align': 'center'
            })

            for (mes, archivo), df_mes in df_final.groupby(["MES", "ARCHIVO"]):

                sheet_name = f"{mes}_{archivo}"[:31]
                df_exportar = df_mes.drop(columns=["MES", "ARCHIVO"])

                df_exportar.to_excel(writer, sheet_name=sheet_name, index=False, startrow=2)
                worksheet = writer.sheets[sheet_name]

                # 🏷 TÍTULO
                worksheet.merge_range(0, 0, 0, len(df_exportar.columns)-1,
                                      f"COMPRAS DE {mes}",
                                      title_format)

                # Encabezados
                for col_num, value in enumerate(df_exportar.columns.values):
                    worksheet.write(2, col_num, value, header_format)

                # Datos
                for row in range(len(df_exportar)):
                    for col in range(len(df_exportar.columns)):

                        value = df_exportar.iloc[row, col]

                        if df_exportar.columns[col] == "FECHA":
                            worksheet.write_datetime(row+3, col, value, date_format)
                        elif df_exportar.columns[col] == "PROVEEDOR":
                            worksheet.write(row+3, col, value, left_format)
                        elif df_exportar.columns[col] == "DESCRIPCIÓN":
                            worksheet.write(row+3, col, value, red_text_format)
                        elif col >= 7 and col <= 11:
                            worksheet.write(row+3, col, value, number_format)
                        else:
                            worksheet.write(row+3, col, value, text_format)

                fila_total = len(df_exportar) + 3

                worksheet.write(fila_total, 0, "TOTAL", header_format)

                for col_idx in range(7, 12):
                    col_letter = chr(65 + col_idx)
                    worksheet.write_formula(
                        fila_total,
                        col_idx,
                        f"=SUM({col_letter}4:{col_letter}{len(df_exportar)+3})",
                        total_format
                    )

                worksheet.freeze_panes(3, 0)
                worksheet.set_column(0, len(df_exportar.columns)-1, 18)

        with open(nombre_excel, "rb") as file:
            st.download_button(
                label="Descargar Excel Profesional",
                data=file,
                file_name=nombre_excel,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    else:
        st.warning("No se pudieron procesar archivos válidos.")



