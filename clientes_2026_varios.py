import streamlit as st
import pandas as pd
import calendar

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

            df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce", dayfirst=True)

            df["BASE 0%"] = df.apply(
                lambda x: x["VALOR SIN IMPUESTOS"] if x["IVA"] == 0 else 0,
                axis=1
            )

            df["BASE 12%"] = df.apply(
                lambda x: x["VALOR SIN IMPUESTOS"] if x["IVA"] != 0 else 0,
                axis=1
            )

            # CLASIFICACIÓN
            def clasificar(proveedor):
                p = str(proveedor).lower()

                if any(x in p for x in [
                    "panificadora","alimentos","carniceria",
                    "restaurant","comida","super","market",
                    "mayflower","buffalo","corporacion favorita"
                ]):
                    return "Gastos alimenticios"

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
        df_final["MES"] = df_final["FECHA"].dt.to_period("M")

        nombre_excel = "compras_formato_profesional.xlsx"

        with pd.ExcelWriter(nombre_excel, engine="xlsxwriter") as writer:

            workbook = writer.book

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

            for mes, df_mes in df_final.groupby("MES"):

                mes_num = mes.month
                año = mes.year
                nombre_mes = calendar.month_name[mes_num].upper()

                titulo = f"COMPRAS {nombre_mes} {año}"

                sheet_name = f"{mes}"[:31]
                df_exportar = df_mes.drop(columns=["MES","ARCHIVO"])

                df_exportar.to_excel(writer, sheet_name=sheet_name, index=False, startrow=3)
                worksheet = writer.sheets[sheet_name]

                # TÍTULO
                worksheet.merge_range(0, 0, 0, len(df_exportar.columns)-1,
                                      titulo, workbook.add_format({
                                          'bold': True,
                                          'align': 'center',
                                          'font_size': 12
                                      }))

                # ENCABEZADOS
                for col_num, value in enumerate(df_exportar.columns.values):
                    if value == "DESCRIPCIÓN":
                        worksheet.write(3, col_num, value, header_plain)
                    else:
                        worksheet.write(3, col_num, value, header_format)

                # DATOS
                for row in range(len(df_exportar)):
                    for col in range(len(df_exportar.columns)):

                        value = df_exportar.iloc[row, col]
                        col_name = df_exportar.columns[col]

                        if col_name == "FECHA":
                            worksheet.write_datetime(row+4, col, value, date_format)

                        elif col_name == "PROVEEDOR":
                            worksheet.write(row+4, col, value, text_left)

                        elif col_name == "DESCRIPCIÓN":
                            worksheet.write(row+4, col, value, descripcion_format)

                        elif col_name in ["BASE 0%","BASE 12%","PROPINA","IVA","TOTAL"]:
                            worksheet.write(row+4, col, value, number_format)

                        else:
                            worksheet.write(row+4, col, value, text_center)

                fila_total = len(df_exportar) + 4
                worksheet.write(fila_total, 0, "TOTAL", total_format)

                for col in range(len(df_exportar.columns)):
                    col_name = df_exportar.columns[col]

                    if col_name == "DESCRIPCIÓN":
                        worksheet.write(fila_total, col, "", descripcion_format)

                    elif col_name in ["BASE 0%","BASE 12%","PROPINA","IVA","TOTAL"]:
                        col_letter = chr(65 + col)
                        worksheet.write_formula(
                            fila_total,
                            col,
                            f"=SUM({col_letter}5:{col_letter}{len(df_exportar)+4})",
                            total_number
                        )

                    else:
                        worksheet.write(fila_total, col, "", total_format)

                worksheet.freeze_panes(4, 0)

                # ANCHOS EXACTOS
                worksheet.set_column(df_exportar.columns.get_loc("FECHA"),
                                     df_exportar.columns.get_loc("FECHA"), 12)

                worksheet.set_column(df_exportar.columns.get_loc("RUC"),
                                     df_exportar.columns.get_loc("RUC"), 14)

                worksheet.set_column(df_exportar.columns.get_loc("FACT"),
                                     df_exportar.columns.get_loc("FACT"), 14)

                worksheet.set_column(df_exportar.columns.get_loc("Clave de acceso"),
                                     df_exportar.columns.get_loc("Clave de acceso"), 40)

                worksheet.set_column(df_exportar.columns.get_loc("PROVEEDOR"),
                                     df_exportar.columns.get_loc("PROVEEDOR"), 30)

                worksheet.set_column(df_exportar.columns.get_loc("DESCRIPCIÓN"),
                                     df_exportar.columns.get_loc("DESCRIPCIÓN"), 22)

        with open(nombre_excel, "rb") as file:
            st.download_button(
                "Descargar Excel Profesional",
                data=file,
                file_name=nombre_excel,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    else:
        st.warning("No se pudieron procesar archivos válidos.")
