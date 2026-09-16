#!/usr/bin/env python3
"""
detector_garrafas.py
Consulta /predict/camera do yolo-api e aciona buzzer + LED (GPIO18)
quando uma garrafa danificada é detectada.
"""

import requests
from gpiozero import DigitalOutputDevice
from time import time, sleep

# ---------------- CONFIG ----------------
API_URL      = "http://100.78.45.107:8000/predict/camera"
MODELO       = "yolo-epi.pt"
CONF_MIN     = 0.3
GPIO_PIN     = 18

TEMPO_ALARME = 0.5     # buzzer + LED ligados por 3s
COOLDOWN     = 1.0     # mínimo entre dois alarmes
INTERVALO    = 0.2     # pausa entre chamadas à API (não conta o tempo da request)

CLASSES_ALVO = {"Garrafa amassada", "Tampa incorreta", "Tampa ausente"}
# ----------------------------------------

saida = DigitalOutputDevice(GPIO_PIN)
alarme_ate    = 0.0
ultimo_alarme = 0.0

print(f"✅ Consultando {API_URL}")
print(f"   Modelo: {MODELO} | confiança mínima: {CONF_MIN}")
print(f"   Classes gatilho: {CLASSES_ALVO}")
print(f"   Alarme: {TEMPO_ALARME}s ON | cooldown {COOLDOWN}s")
print("   Ctrl+C para sair.\n")

try:
    while True:
        detectou = False
        alvos = []

        try:
            r = requests.post(
                API_URL,
                params={"model_name": MODELO, "confidence": CONF_MIN},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()

            for d in data.get("detections", []):
                if d["label"] in CLASSES_ALVO and d["confidence"] >= CONF_MIN:
                    detectou = True
                    alvos.append(f"{d['label']}({d['confidence']:.2f})")

        except Exception as e:
            print(f"[api] erro: {e}")

        agora = time()

        if detectou and (agora - ultimo_alarme) > COOLDOWN:
            ultimo_alarme = agora
            alarme_ate = agora + TEMPO_ALARME
            print(f"[{agora:.2f}] 🚨 {' | '.join(alvos)} | alarme ON por {TEMPO_ALARME}s")

        if agora < alarme_ate:
            saida.on()
        else:
            saida.off()

        sleep(INTERVALO)

except KeyboardInterrupt:
    print("\nEncerrado.")

finally:
    saida.off()
    saida.close()
    print("Saída GPIO desligada. Tchau!")
