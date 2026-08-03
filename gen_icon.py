import os
import shutil
import subprocess

from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
SVG = os.path.join(BASE, "icon.svg")
PNG = os.path.join(BASE, "icon.png")
ICO = os.path.join(BASE, "icon.ico")
EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

uri = "file:///" + SVG.replace("\\", "/")
edge = next((p for p in EDGE_CANDIDATES if os.path.exists(p)), None)
if edge is None:
    raise SystemExit("Nenhum Edge/Chrome encontrado para renderizar o SVG.")

profile = os.path.join(os.environ["TEMP"], "akp-edge-profile")
if os.path.exists(profile):
    shutil.rmtree(profile)

subprocess.run(
    [edge, "--headless", "--disable-gpu", "--user-data-dir=" + profile,
     "--screenshot=" + PNG, "--window-size=256,256",
     "--default-background-color=00000000", uri],
    check=True, capture_output=True,
)

img = Image.open(PNG).convert("RGBA")
img.save(ICO, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
print("icon.png / icon.ico gerados a partir de icon.svg")
