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
                "CLAVE_ACCESO": "FACT",
                "IMPORTE_TOTAL": "TOTAL"
            })

            df["IVA"] = pd.to_numeric(df.get("IVA", 0), errors="coerce").fillna(0)
            df["VALOR SIN IMPUESTOS"] = pd.to_numeric(
                df["VALOR SIN IMPUESTOS"], errors="coerce"
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

            columnas_ordenadas = [
                "FECHA",
                "PROVEEDOR",
                "RUC",
                "FACT",
                "BASE 0%",
                "BASE 12%",
                "IVA",
                "TOTAL"
            ]

            for col in columnas_ordenadas:
                if col not in df.columns:
                    df[col] = 0

            df = df[columnas_ordenadas]

            # 🔥 AGREGAMOS NOMBRE DEL ARCHIVO
            df["ARCHIVO"] = archivo.name.replace(".txt", "")

            dfs.append(df)

        except Exception as e:
            st.error(f"Error procesando {archivo.name}: {e}")

    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)

        df_final["MES"] = df_final["FECHA"].dt.to_period("M").astype(str)

        st.success("Archivos procesados correctamente")

        st.dataframe(df_final)

        nombre_excel = "compras_separadas_por_mes_y_archivo.xlsx"

        with pd.ExcelWriter(nombre_excel, engine="xlsxwriter") as writer:
            for (mes, archivo), df_mes in df_final.groupby(["MES", "ARCHIVO"]):

                sheet_name = f"{mes}_{archivo}"[:31]  # Excel máximo 31 caracteres

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
