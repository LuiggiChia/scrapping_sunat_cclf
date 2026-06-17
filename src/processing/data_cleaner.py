import datetime
import pandas as pd


def clean_data(df: pd.DataFrame) -> pd.DataFrame:

    mask = df["domicilio_fiscal"].isna() | (df["domicilio_fiscal"].str.strip() == "")

    df["domicilio_fiscal"] = df["domicilio_fiscal"].fillna("")

    parts = df["domicilio_fiscal"].str.rsplit(" - ", n=2, expand=True).reindex(columns=range(3), fill_value="")

    df["domicilio_fiscal_detalle"] = "-"
    df["provincia"] = "-"
    df["distrito"] = "-"
    df["departamento"] = "-"
    df["direccion"] = "-"

    df.loc[~mask, "domicilio_fiscal_detalle"] = parts[0]
    df.loc[~mask, "provincia"] = parts[1]
    df.loc[~mask, "distrito"] = parts[2]

    df.loc[~mask, "departamento"] = df.loc[~mask, "domicilio_fiscal_detalle"].str.split().str[-1]
    df.loc[~mask, "direccion"] = df.loc[~mask, "domicilio_fiscal_detalle"].str.split().str[:-1].str.join(" ")

    df = df.drop(columns=["domicilio_fiscal_detalle"])

    if "actividades_secundarias" in df.columns:

        df["actividades_secundarias"] = df["actividades_secundarias"].apply(
            lambda x: x if isinstance(x, list) else []
        )

        df["actividad_secundaria_1"] = df["actividades_secundarias"].str[0]
        df["actividad_secundaria_2"] = df["actividades_secundarias"].str[1]
        df["actividad_secundaria_3"] = df["actividades_secundarias"].str[2]

        df = df.drop(columns=["actividades_secundarias"])

    df["fecha_ejecucion"] = datetime.datetime.now()

    for col in ["fecha_inscripcion", "fecha_inicio_actividades"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df[col] = df[col].apply(lambda x: None if pd.isna(x) else x)

    text_columns = [
        "ruc",
        "razon_social",
        "tipo_contribuyente",
        "nombre_comercial",
        "direccion",
        "departamento",
        "provincia",
        "distrito",
        "actividad_comercio_exterior",
        "sistema_contabilidad",
        "actividad_principal",
        "actividad_secundaria_1",
        "actividad_secundaria_2",
        "actividad_secundaria_3",
        "domicilio_fiscal",
        "estado_contribuyente",
        "condicion_contribuyente",
    ]

    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype("string")

    ordered_columns = [
        "fecha_ejecucion",
        "ruc",
        "razon_social",
        "tipo_contribuyente",
        "nombre_comercial",
        "fecha_inscripcion",
        "fecha_inicio_actividades",
        "estado_contribuyente",
        "condicion_contribuyente",
        "direccion",
        "departamento",
        "provincia",
        "distrito",
        "actividad_comercio_exterior",
        "sistema_contabilidad",
        "actividad_principal",
        "actividad_secundaria_1",
        "actividad_secundaria_2",
        "actividad_secundaria_3",
        "domicilio_fiscal",
    ]

    df = df[ordered_columns]

    df = df.astype(object).where(pd.notnull(df), None)

    return df
