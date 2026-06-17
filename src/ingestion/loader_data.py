import os
import psycopg2
import paramiko
import pandas as pd
from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder
from psycopg2.extras import execute_values

if not hasattr(paramiko, "DSSKey"):
    paramiko.DSSKey = paramiko.PKey


def get_db_connection(logger, base_dir):

    env_path = os.path.join(base_dir, "config", ".env")
    load_dotenv(env_path)

    required_vars = [
        "SSH_HOST",
        "SSH_USER",
        "SSH_PKEY",
        "DB_HOST",
        "DB_NAME",
        "DB_USER",
        "DB_PASS",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise ValueError(f"Faltan variables de entorno: {', '.join(missing_vars)}")

    ssh_host = os.getenv("SSH_HOST")
    ssh_user = os.getenv("SSH_USER")
    ssh_pkey = os.path.join(base_dir, "config", os.getenv("SSH_PKEY"))

    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")

    server = SSHTunnelForwarder(
        (ssh_host, 22),
        ssh_username=ssh_user,
        ssh_pkey=ssh_pkey,
        remote_bind_address=(db_host, 5432),
        set_keepalive=30,
    )

    server.start()

    logger.info(f"Túnel SSH iniciado en puerto local: {server.local_bind_port}")

    conn = psycopg2.connect(
        host="127.0.0.1",
        port=server.local_bind_port,
        user=db_user,
        password=db_pass,
        database=db_name,
        connect_timeout=10,
    )

    logger.info("Conexión a PostgreSQL exitosa")

    return conn, server


def upsert_sunat(conn, df, logger):

    df = df.where(pd.notnull(df), None)

    query = """
        INSERT INTO toquea_sunat.dm_clientes_sunat (
            fecha_ejecucion,
            ruc,
            razon_social,
            tipo_contribuyente,
            nombre_comercial,
            fecha_inscripcion,
            fecha_inicio_actividades,
            estado_contribuyente,
            condicion_contribuyente,
            direccion,
            departamento,
            provincia,
            distrito,
            actividad_comercio_exterior,
            sistema_contabilidad,
            actividad_principal,
            actividad_secundaria_1,
            actividad_secundaria_2,
            actividad_secundaria_3,
            domicilio_fiscal
        )
        VALUES %s
        ON CONFLICT (ruc)
        DO UPDATE SET
            fecha_ejecucion = EXCLUDED.fecha_ejecucion,
            razon_social = EXCLUDED.razon_social,
            tipo_contribuyente = EXCLUDED.tipo_contribuyente,
            nombre_comercial = EXCLUDED.nombre_comercial,
            fecha_inscripcion = EXCLUDED.fecha_inscripcion,
            fecha_inicio_actividades = EXCLUDED.fecha_inicio_actividades,
            estado_contribuyente = EXCLUDED.estado_contribuyente,
            condicion_contribuyente = EXCLUDED.condicion_contribuyente,
            direccion = EXCLUDED.direccion,
            departamento = EXCLUDED.departamento,
            provincia = EXCLUDED.provincia,
            distrito = EXCLUDED.distrito,
            actividad_comercio_exterior = EXCLUDED.actividad_comercio_exterior,
            sistema_contabilidad = EXCLUDED.sistema_contabilidad,
            actividad_principal = EXCLUDED.actividad_principal,
            actividad_secundaria_1 = EXCLUDED.actividad_secundaria_1,
            actividad_secundaria_2 = EXCLUDED.actividad_secundaria_2,
            actividad_secundaria_3 = EXCLUDED.actividad_secundaria_3,
            domicilio_fiscal = EXCLUDED.domicilio_fiscal;
    """

    values = [
        (
            r.get("fecha_ejecucion"),
            r.get("ruc"),
            r.get("razon_social"),
            r.get("tipo_contribuyente"),
            r.get("nombre_comercial"),
            r.get("fecha_inscripcion"),
            r.get("fecha_inicio_actividades"),
            r.get("estado_contribuyente"),
            r.get("condicion_contribuyente"),
            r.get("direccion"),
            r.get("departamento"),
            r.get("provincia"),
            r.get("distrito"),
            r.get("actividad_comercio_exterior"),
            r.get("sistema_contabilidad"),
            r.get("actividad_principal"),
            r.get("actividad_secundaria_1"),
            r.get("actividad_secundaria_2"),
            r.get("actividad_secundaria_3"),
            r.get("domicilio_fiscal"),
        )
        for r in df.to_dict(orient="records")
    ]

    try:
        with conn.cursor() as cur:
            execute_values(cur, query, values, page_size=1000)
        conn.commit()

        logger.info(f"UPSERT completado: {len(df)} registros")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error en UPSERT: {e}")
        raise


def resume_process(conn, lst_rucs, logger):

    query = """
        SELECT ruc
        FROM toquea_sunat.dm_clientes_sunat
    """

    df_bd = pd.read_sql(query, conn)

    rucs_excel = set(map(str, lst_rucs))
    rucs_bd = set(df_bd["ruc"].astype(str))

    missing_rucs = list(rucs_excel - rucs_bd)

    logger.info(f"RUCs Excel: {len(rucs_excel)}")
    logger.info(f"RUCs procesados: {len(rucs_bd)}")
    logger.info(f"RUCs pendientes: {len(missing_rucs)}")

    return missing_rucs
