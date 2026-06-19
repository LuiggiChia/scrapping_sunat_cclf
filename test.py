import random
import time
import datetime
import pandas as pd
from playwright.sync_api import Playwright, sync_playwright


def sunat_consultation(playwright: Playwright, valor: str) -> dict | None:

    browser = playwright.chromium.launch(headless=True)

    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1366, "height": 768},
    )

    page = context.new_page()

    try:
        print(f"Se está realizando la consulta: {valor} ...")

        page.goto("https://e-consultaruc.sunat.gob.pe/", wait_until="networkidle")

        page.wait_for_selector("#btnPorRuc", timeout=10000)

        page.locator("#btnPorRuc").click()

        page.locator("#txtRuc").press_sequentially(valor, delay=random.randint(80, 150))

        time.sleep(random.uniform(1.0, 2.5))

        page.locator("#btnAceptar").click()

        page.wait_for_timeout(3000)

        page.locator('.btn.btn-primary.btn-sm.btnInfDeuCoa').click()
        page.wait_for_timeout(3000)

        text = page.locator("body").inner_text()

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        # Inicializamos la estructura de datos base
        data_deuda_coactiva = {
            "ruc": valor,  # Se predefine con el valor de la consulta por seguridad
            "tiene_deuda_coactiva": False,
            "deudas": []
        }

        # 1. Extraer RUC y Razón Social buscando en toda la lista de líneas
        for line in lines:
            if "DEUDA COACTIVA REMITIDA A CENTRALES DE RIESGO DE" in line:
                info_contribuyente = line.replace("DEUDA COACTIVA REMITIDA A CENTRALES DE RIESGO DE ", "")
                ruc, razon_social = info_contribuyente.split(" - ", 1)
                data_deuda_coactiva["ruc"] = ruc.strip()
                break

        # 2. Evaluar los escenarios de deuda
        # ESCENARIO A: No registra deudas
        if "No se ha remitido deuda en cobranza coactiva que corresponda al contribuyente consultado." in lines:
            data_deuda_coactiva["tiene_deuda_coactiva"] = False

        # ESCENARIO B: Sí registra deudas (Procesamos la tabla tabulada)
        elif "Monto de la Deuda\tPeríodo Tributario\tFecha de Inicio de Cobranza Coactiva\tEntidad Asociada a la Deuda" in lines:
            data_deuda_coactiva["tiene_deuda_coactiva"] = True
            
            # Buscamos en qué índice está la cabecera de la tabla
            indice_cabecera = lines.index("Monto de la Deuda\tPeríodo Tributario\tFecha de Inicio de Cobranza Coactiva\tEntidad Asociada a la Deuda")
            
            # Recorremos las líneas siguientes a la cabecera
            for line in lines[indice_cabecera + 1:]:
                if "\t" not in line:
                    break
                    
                campos = line.split("\t")
                
                deuda_info = {
                    "ruc": data_deuda_coactiva["ruc"],
                    "tiene_deuda": "SI",
                    "monto": float(campos[0]),
                    "periodo": campos[1].strip(),
                    "fecha_inicio": campos[2].strip(),
                    "entidad": campos[3].strip()
                }
                data_deuda_coactiva["deudas"].append(deuda_info)

        # ESCENARIO C: Si no se añadieron deudas (RUC limpio), insertamos la fila con guiones
        if not data_deuda_coactiva["deudas"]:
            deuda_vacia = {
                "ruc": data_deuda_coactiva["ruc"],
                "tiene_deuda": "NO",
                "monto": None,
                "periodo": None,
                "fecha_inicio": None,
                "entidad": None
            }
            data_deuda_coactiva["deudas"].append(deuda_vacia)
            
        return data_deuda_coactiva["deudas"]

    except Exception as e:
        print(f"Error durante la consulta {valor}: {e}")
        return None

    finally:
        context.close()
        browser.close()

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df['fecha_inicio'] = pd.to_datetime(df['fecha_inicio'], dayfirst=True, errors='coerce')
    return df


results = []

if __name__ == "__main__":
    with sync_playwright() as p:
        # Prueba con el RUC sin deuda
        for i in ["10754886795", "10425802394"]:
            registro = sunat_consultation(playwright=p, valor=i)
            print(registro)
            results.extend(registro)
        df = pd.DataFrame(results)
        df["fecha_ejecucion"] = datetime.datetime.now()
        df['fecha_inicio'] = pd.to_datetime(df['fecha_inicio'], dayfirst=True, errors='coerce')
        df = df[["fecha_ejecucion", "ruc", "tiene_deuda", "monto", "periodo", "fecha_inicio", "entidad"]]
        df = df.where(pd.notnull(df), None)
        print(df.dtypes)
        print(df)
