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

            # FACT solo número (serie)
            df["FACT"] = df.get("Serie", "").astype(str)

            # Convertir valores numéricos
            df["IVA"] = pd.to_numeric(df.get("IVA", 0), errors="coerce").fillna(0)

            df["VALOR SIN IMPUESTOS"] = pd.to_numeric(
                df.get("VALOR SIN IMPUESTOS", 0),
                errors="coerce"
            ).fillna(0)

            # Fecha sin hora
            df["FECHA"] = pd.to_datetime(
                df.get("FECHA"),
                errors="coerce",
                dayfirst=True
            ).dt.date

            # Bases
            df["BASE 0%"] = df.apply(
                lambda x: x["VALOR SIN IMPUESTOS"] if x["IVA"] == 0 else 0,
                axis=1
            )

            df["BASE 12%"] = df.apply(
                lambda x: x["VALOR SIN IMPUESTOS"] if x["IVA"] != 0 else 0,
                axis=1
            )

            # Columnas que deben ir vacías
            df["NO OBJETO"] = None
            df["EXCENTO IVA"] = None
            df["PROPINA"] = None

            columnas_finales = [
                "FECHA",
                "PROVEEDOR",
                "RUC",
                "FACT",
                "Clave de acceso",
                "NO OBJETO",
                "EXCENTO IVA",
                "BASE 0%",
                "BASE 12%",
                "PROPINA",
                "IVA",
                "TOTAL"
            ]

            for col in columnas_finales:
                if col not in df.columns:
                    df[col] = None

            df = df[columnas_finales]

            # Guardar nombre archivo
            df["ARCHIVO"] = archivo.name.replace(".txt", "")

            dfs.append(df)

        except Exception as e:
            st.error(f"Error procesando {archivo.name}: {e}")

    if dfs:

        df_final = pd.concat(dfs, ignore_index=True)

        # Crear MES correctamente (sin error)
        df_final["MES"] = pd.to_datetime(
            df_final["FECHA"],
            errors="coerce"
        ).dt.to_period("M").astype(str)

        st.success("Archivos procesados correctamente")

        st.dataframe(df_final)

        nombre_excel = "compras_separadas_por_mes_y_archivo.xlsx"

        with pd.ExcelWriter(nombre_excel, engine="xlsxwriter") as writer:

            for (mes, archivo), df_mes in df_final.groupby(["MES", "ARCHIVO"]):

                sheet_name = f"{mes}_{archivo}"[:31]

                df_mes.drop(columns=["MES", "ARCHIVO"]).to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False
                )

        with open(nombre_excel, "rb") as file:
            st.download_button(
                label="Descargar Excel separado por mes y archivo",
                data=file,
                file_name=nombre_excel,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    else:
        st.warning("No se pudieron procesar archivos válidos.")


