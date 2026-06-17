import datetime
import pandas as pd

# rut_cliente y rut_deudor (agrego cliente)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:

    # --- DOMICILIO ---
    df["domicilio_fiscal"] = df["domicilio_fiscal"].fillna("")

    parts = df["domicilio_fiscal"].str.rsplit(" - ", n=2, expand=True)

    df["domicilio_fiscal_detalle"] = parts[0]
    df["provincia"] = parts[1]
    df["distrito"] = parts[2]

    df["departamento"] = df["domicilio_fiscal_detalle"].str.split().str[-1]

    df["direccion"] = df["domicilio_fiscal_detalle"].str.split().str[:-1].str.join(" ")

    df = df.drop(columns=["domicilio_fiscal_detalle"])

    # --- ACTIVIDADES SECUNDARIAS ---
    if "actividades_secundarias" in df.columns:

        df["actividades_secundarias"] = df["actividades_secundarias"].apply(
            lambda x: x if isinstance(x, list) else []
        )

        df["actividad_secundaria_1"] = df["actividades_secundarias"].str[0]
        df["actividad_secundaria_2"] = df["actividades_secundarias"].str[1]
        df["actividad_secundaria_3"] = df["actividades_secundarias"].str[2]

        df = df.drop(columns=["actividades_secundarias"])
        df["fecha_ejecucion"] = datetime.datetime.now()
        df["fecha_inscripcion"] = pd.to_datetime(
            df["fecha_inscripcion"], errors="coerce"
        )
        df["fecha_inicio_actividades"] = pd.to_datetime(
            df["fecha_inicio_actividades"], errors="coerce"
        )

        text_columns = [
            "ruc",
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
        ]

        df[text_columns] = df[text_columns].astype("str")

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
        df = df.where(pd.notnull(df), None)

        print(df.dtypes)

    return df
