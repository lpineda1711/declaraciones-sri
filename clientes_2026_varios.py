import streamlit as st
import pandas as pd
import calendar

st.set_page_config(page_title="Procesador Compras SRI", layout="wide")

st.title("Procesador de Compras")

uploaded_files = st.file_uploader(
    "Sube tus archivos TXT",
    type="txt",
    accept_multiple_files=True
)

if uploaded_files:

    nombre_excel = "compras_consolidado.xlsx"

    with pd.ExcelWriter(nombre_excel, engine="xlsxwriter") as writer:

        workbook = writer.book

        # FORMATOS
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#FFFF00',
            'border': 1,
            'align': 'center'
        })

        header_plain = workbook.add_format({
            'bold': True,
            'align': 'center'
        })

        text_left = workbook.add_format({
            'border': 1,
            'align': 'left'
        })

        text_center = workbook.add_format({
            'border': 1,
            'align': 'center'
        })

        descripcion_format = workbook.add_format({
            'font_color': 'red',
            'align': 'left'
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
            'align': 'center'
        })

        total_number = workbook.add_format({
            'bold': True,
            'bg_color': '#FFFF00',
            'border': 1,
            'num_format': '#,##0.00',
            'align': 'center'
        })

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

                df["TOTAL"] = pd.to_numeric(df.get("TOTAL", 0), errors="coerce").fillna(0)

                df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce", dayfirst=True)

                df["BASE 0%"] = df.apply(
                    lambda x: x["VALOR SIN IMPUESTOS"] if x["IVA"] == 0 else 0,
                    axis=1
                )

                df["BASE 12%"] = df.apply(
                    lambda x: x["VALOR SIN IMPUESTOS"] if x["IVA"] != 0 else 0,
                    axis=1
                )

                def clasificar(proveedor):
                    p = str(proveedor).lower()

                    if any(x in p for x in [
                        "panificadora","alimentos","carniceria",
                        "restaurant","comida","super","market",
                        "mayflower","buffalo","corporacion favorita"
                    ]):
                        return "Alimentación"

                    if any(x in p for x in [
                        "autoservicio","gas","estacion",
                        "petro","fuel","diesel","conauto"
                    ]):
                        return "Combustible"

                    if any(x in p for x in [
                        "farmacia","medic","hospital",
                        "clinica","laboratorio"
                    ]):
                        return "Médicos"

                    return "Otros gastos"

                df_final = pd.DataFrame()
                df_final["FECHA"] = df["FECHA"]
                df_final["PROVEEDOR"] = df["PROVEEDOR"]
                df_final["RUC"] = df["RUC"]
                df_final["FACT"] = df["FACT"]
                df_final["Clave de acceso"] = df["Clave de acceso"]
                df_final["NO OBJETO"] = ""
                df_final["EXCENTO DE IVA"] = ""
                df_final["BASE 0%"] = df["BASE 0%"]
                df_final["BASE 12%"] = df["BASE 12%"]
                df_final["PROPINA"] = 0
                df_final["IVA"] = df["IVA"]
                df_final["TOTAL"] = df["TOTAL"]
                df_final["DESCRIPCIÓN"] = df_final["PROVEEDOR"].apply(clasificar)

                # Nombre hoja = nombre archivo
                sheet_name = archivo.name.replace(".txt", "")[:31]

                worksheet = workbook.add_worksheet(sheet_name)
                writer.sheets[sheet_name] = worksheet

                # Título según mes
                primera_fecha = df_final["FECHA"].dropna().iloc[0]
                mes = primera_fecha.month
                año = primera_fecha.year
                nombre_mes = calendar.month_name[mes].upper()

                titulo = f"COMPRAS {nombre_mes} {año}"

                worksheet.merge_range(0, 0, 0, len(df_final.columns)-1,
                                      titulo,
                                      workbook.add_format({
                                          'bold': True,
                                          'align': 'center',
                                          'font_size': 12
                                      }))

                # Encabezados
                for col_num, value in enumerate(df_final.columns.values):
                    if value == "DESCRIPCIÓN":
                        worksheet.write(1, col_num, value, header_plain)
                    else:
                        worksheet.write(1, col_num, value, header_format)

                # Datos
                for row in range(len(df_final)):
                    for col in range(len(df_final.columns)):

                        value = df_final.iloc[row, col]
                        col_name = df_final.columns[col]

                        if col_name == "FECHA":
                            worksheet.write_datetime(row+2, col, value, date_format)
                        elif col_name == "PROVEEDOR":
                            worksheet.write(row+2, col, value, text_left)
                        elif col_name == "DESCRIPCIÓN":
                            worksheet.write(row+2, col, value, descripcion_format)
                        elif col_name in ["BASE 0%","BASE 12%","PROPINA","IVA","TOTAL"]:
                            worksheet.write(row+2, col, value, number_format)
                        else:
                            worksheet.write(row+2, col, value, text_center)

                # Totales
                fila_total = len(df_final) + 2
                worksheet.write(fila_total, 0, "TOTAL", total_format)

                for col in range(len(df_final.columns)):
                    col_name = df_final.columns[col]

                    if col_name == "DESCRIPCIÓN":
                        worksheet.write(fila_total, col, "", descripcion_format)
                    elif col_name in ["BASE 0%","BASE 12%","PROPINA","IVA","TOTAL"]:
                        col_letter = chr(65 + col)
                        worksheet.write_formula(
                            fila_total,
                            col,
                            f"=SUM({col_letter}3:{col_letter}{len(df_final)+2})",
                            total_number
                        )
                    else:
                        worksheet.write(fila_total, col, "", total_format)

                worksheet.freeze_panes(2, 0)

                # Anchos
                worksheet.set_column(0, 0, 12)
                worksheet.set_column(1, 1, 30)
                worksheet.set_column(2, 2, 14)
                worksheet.set_column(3, 3, 14)
                worksheet.set_column(4, 4, 40)
                worksheet.set_column(12, 12, 20)

            except Exception as e:
                st.error(f"Error procesando {archivo.name}: {e}")

    with open(nombre_excel, "rb") as file:
        st.download_button(
            "Descargar Excel",
            data=file,
            file_name=nombre_excel,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
