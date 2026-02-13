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

            text_format = workbook.add_format({'border': 1})

            date_format = workbook.add_format({
                'border': 1,
                'num_format': 'dd/mm/yyyy'
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

                # Encabezados
                for col_num, value in enumerate(df_exportar.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                # Datos
                for row in range(len(df_exportar)):
                    for col in range(len(df_exportar.columns)):

                        value = df_exportar.iloc[row, col]

                        if col == 0:
                            worksheet.write_datetime(row+1, col, value, date_format)
                        elif col >= 5:
                            worksheet.write(row+1, col, value, number_format)
                        else:
                            worksheet.write(row+1, col, value, text_format)

                # Fila TOTAL
                fila_total = len(df_exportar) + 1

                for col in range(len(df_exportar.columns)):
                    worksheet.write(fila_total, col, "", total_text_format)

                worksheet.write(fila_total, 0, "TOTAL", total_text_format)

                for col_idx in range(5, 10):
                    col_letter = chr(65 + col_idx)
                    worksheet.write_formula(
                        fila_total,
                        col_idx,
                        f"=SUM({col_letter}2:{col_letter}{len(df_exportar)+1})",
                        total_format
                    )

                worksheet.freeze_panes(1, 0)
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






