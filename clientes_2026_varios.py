if dfs:
    df_final = pd.concat(dfs, ignore_index=True)

    df_final["MES"] = df_final["FECHA"].dt.to_period("M").astype(str)

    st.success("Archivos procesados correctamente")
    st.dataframe(df_final)

    nombre_excel = "compras_separadas_por_mes_y_archivo.xlsx"

    with pd.ExcelWriter(nombre_excel, engine="xlsxwriter") as writer:

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

                df["MES"] = df["FECHA"].dt.to_period("M").astype(str)

                nombre_archivo = archivo.name.replace(".txt", "")[:15]

                for mes, df_mes in df.groupby("MES"):
                    sheet_name = f"{mes}_{nombre_archivo}"[:31]  # Excel máximo 31 caracteres
                    df_mes.drop(columns="MES").to_excel(
                        writer,
                        sheet_name=sheet_name,
                        index=False
                    )

            except Exception as e:
                st.error(f"Error procesando {archivo.name}: {e}")
