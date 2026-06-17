import datetime
import pandas as pd


def clean_data(df: pd.DataFrame) -> pd.DataFrame:

    df["domicilio_fiscal"] = df["domicilio_fiscal"].fillna("-").str.strip()

    parts = (
        df["domicilio_fiscal"]
        .str.rsplit(" - ", n=2, expand=True)
        .reindex(columns=range(3), fill_value="-")
    )

    df["domicilio_fiscal_detalle"] = parts[0].fillna("-")
    df["provincia"] = parts[1].fillna("-")
    df["distrito"] = parts[2].fillna("-")

    df["departamento"] = df["domicilio_fiscal_detalle"].str.split().str[-1].fillna("-")
    df["direccion"] = df["domicilio_fiscal_detalle"].str.split().str[:-1].str.join(" ").fillna("-")

    df.loc[df["direccion"] == "", "direccion"] = "-"
    df.loc[df["departamento"] == "", "departamento"] = "-"

    df = df.drop(columns=["domicilio_fiscal_detalle"])

    df["actividad_secundaria_1"] = "-"
    df["actividad_secundaria_2"] = "-"
    df["actividad_secundaria_3"] = "-"

    if "actividades_secundarias" in df.columns:

        df["actividades_secundarias"] = df["actividades_secundarias"].apply(
            lambda x: x if isinstance(x, list) else []
        )

        df["actividad_secundaria_1"] = df["actividades_secundarias"].str[0].fillna("-")
        df["actividad_secundaria_2"] = df["actividades_secundarias"].str[1].fillna("-")
        df["actividad_secundaria_3"] = df["actividades_secundarias"].str[2].fillna("-")

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

    for col in ordered_columns:
        if col not in df.columns:
            df[col] = "-"

    df = df[ordered_columns]

    df = df.astype(object).where(pd.notnull(df), None)

    return df
