import os
import time
import random
import logging
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright
import warnings

warnings.filterwarnings("ignore")

from src.extraction.drive_reader import (
    load_google_credentials,
    create_drive_service,
    get_reporte_giros_factoring,
)

from src.extraction.sunat_scraper import sunat_consultation

from src.processing.data_cleaner import clean_data

from src.ingestion.loader_data import get_db_connection, upsert_sunat, resume_process

base_dir = os.path.dirname(os.path.abspath(__file__))

log_filename = f"ejecucion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logs_path = os.path.join(base_dir, "logs")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(logs_path, log_filename), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


if __name__ == "__main__":

    BATCH_SIZE = 10

    RESUME_PROCESS = False

    TYPE_USER = "DEUDOR"

    folder_id = "19qttOpGgAZGo6pgqsW4wSHkrGxIg2nrV"
    file_name = "Reporte_Giros_Factoring.xlsx"

    credentials = load_google_credentials(base_dir)

    drive_service = create_drive_service(credentials)

    df_factoring = get_reporte_giros_factoring(drive_service, folder_id, file_name)

    if df_factoring is None:
        raise ValueError("No se pudo obtener el archivo de Drive.")

    unique_rucs = df_factoring["rut_cliente"].dropna().astype(str).unique().tolist()

    print(f"Total RUCs únicos encontrados: {len(unique_rucs)}")

    conn, server = get_db_connection(logger, base_dir)

    if RESUME_PROCESS:
        unique_rucs = resume_process(conn, unique_rucs, logger)

    if not unique_rucs:
        logger.info("No hay RUCs pendientes por procesar")
        conn.close()
        server.stop()
        exit()

    with sync_playwright() as p:

        for batch_start in range(0, len(unique_rucs), BATCH_SIZE):

            batch = unique_rucs[batch_start : batch_start + BATCH_SIZE]

            results = []

            for position, ruc in enumerate(batch, start=1):

                company = sunat_consultation(playwright=p, valor=ruc)

                if company is not None:
                    results.append(company)

                time.sleep(random.uniform(5, 15))

            if results:
                df = pd.DataFrame(results)
                df_clean = clean_data(df)
                df_clean["tipo_usuario"] == TYPE_USER

                upsert_sunat(conn, df_clean, logger)

            time.sleep(random.uniform(300, 360))

    conn.close()
    server.stop()

    print("\nProceso finalizado correctamente.")
