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
                "SERIE_COMPROBANTE": "Serie",
                "IMPORTE_TOTAL": "TOTAL"
            })

            df["FACT"] = df.get("Serie", "").astype(str)

            df["IVA"] = pd.to_numeric(df.get("IVA", 0), errors="coerce").fillna(0)
            df["VALOR SIN IMPUESTOS"] = pd.to_numeric(
                df.get("VALOR SIN IMPUESTOS", 0),
                errors="coerce"
            ).fillna(0)

            df["FECHA"] = pd.to_datetime(
                df.get("FECHA"),
                errors="coerce",
                dayfirst=True
            ).dt.date

            df["BASE 0%"] = df.apply(
                lambda x: x["VALOR SIN IMPUESTOS"] if x["IVA"] == 0 else 0,
                axis=1
            )

            df["BASE 12%"] = df.apply(
                lambda x: x["VALOR SIN IMPUESTOS"] if x["IVA"] != 0 else 0,
                axis=1
            )

            df_limpio = pd.DataFrame()

            df_limpio["FECHA"] = df["FECHA"]
            df_limpio["PROVEEDOR"] = df["PROVEEDOR"]
            df_limpio["RUC"] = df["RUC"]
            df_limpio["FACT"] = df["FACT"]
            df_limpio["Clave de acceso"] = df["Clave de acceso"]
            df_limpio["BASE 0%"] = df["BASE 0%"]
            df_limpio["BASE 12%"] = df["BASE 12%"]
            df_limpio["PROPINA"] = 0
            df_limpio["IVA"] = df["IVA"]
            df_limpio["TOTAL"] = df["TOTAL"]

            df_limpio["ARCHIVO"] = archivo.name.replace(".txt", "")
            dfs.append(df_limpio)

        except Exception as e:
            st.error(f"Error procesando {archivo.name}: {e}")

    if dfs:

        df_final = pd.concat(dfs, ignore_index=True)

        df_final["MES"] = pd.to_datetime(
            df_final["FECHA"],
            errors="coerce"
        ).dt.to_period("M").astype(str)

        st.success("Archivos procesados correctamente")
        st.dataframe(df_final)

        nombre_excel = "compras_formato_profesional.xlsx"

        with pd.ExcelWriter(nombre_excel, engine="xlsxwriter") as writer:

            workbook = writer.book

            # 🎨 FORMATOS
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#FFFF00',
                'border': 1,
                'align': 'center'
            })

            cell_format = workbook.add_format({
                'border': 1
            })

            number_format = workbook.add_format({
                'border': 1,
                'num_format': '#,##0.00'
            })

            total_format = workbook.add_format({
                'bold': True,
                'bg_color': '#FFFF00',
                'border': 1,
                'num_format': '#,##0.00'
            })

            total_text_format = workbook.add_format({
                'bold': True,
                'bg_color': '#FFFF00',
                'border': 1
            })

            for (mes, archivo), df_mes in df_final.groupby(["MES", "ARCHIVO"]):

                sheet_name = f"{mes}_{archivo}"[:31]
                df_exportar = df_mes.drop(columns=["MES", "ARCHIVO"])

                df_exportar.to_excel(writer, sheet_name=sheet_name, index=False)

                worksheet = writer.sheets[sheet_name]

                # Aplicar formato encabezado
                for col_num, value in enumerate(df_exportar.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                # Aplicar bordes y formato número
                for row in range(1, len(df_exportar) + 1):
                    for col in range(len(df_exportar.columns)):
                        if col >= 5:  # columnas numéricas
                            worksheet.write(row, col, df_exportar.iloc[row-1, col], number_format)
                        else:
                            worksheet.write(row, col, df_exportar.iloc[row-1, col], cell_format)

                # Fila total
                fila_total = len(df_exportar) + 1
                worksheet.write(fila_total, 0, "TOTAL", total_text_format)

                columnas_sumar = {
                    5: "BASE 0%",
                    6: "BASE 12%",
                    7: "PROPINA",
                    8: "IVA",
                    9: "TOTAL"
                }

                for col_idx in columnas_sumar.keys():
                    col_letter = chr(65 + col_idx)
                    worksheet.write_formula(
                        fila_total,
                        col_idx,
                        f"=SUM({col_letter}2:{col_letter}{len(df_exportar)+1})",
                        total_format
                    )

        with open(nombre_excel, "rb") as file:
            st.download_button(
                label="Descargar Excel Formato Profesional",
                data=file,
                file_name=nombre_excel,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    else:
        st.warning("No se pudieron procesar archivos válidos.")





