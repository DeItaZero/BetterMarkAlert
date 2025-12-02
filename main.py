import asyncio
import json
import os
import time

import requests
from telegram import Bot
from marks import MarkAlert
from custom_types import *
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import dotenv

dotenv.load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROUP_CHAT_ID = os.environ.get("GROUP_CHAT_ID")
bot = Bot(token=BOT_TOKEN)

# Run this on https://selfservice.campus-dual.de/acwork/cancelproc:
r"""
let trs = Array.from(document.querySelectorAll("tr.expanded")).slice(1);

let modules = trs.map(tr => {
    let texts = Array.from(tr.querySelectorAll("strong")).map(el => el.textContent.trim());
    let [mod, , per, year] = texts;

    // Modulcode aus den Klammern holen
    let match = mod.match(/\(([^)]+)\)$/);
    let moduleCode = match ? match[1] : mod;

    // Period mapping
    let periodCode = per.includes("Winter") ? "001" : "002";

    // Jahr nur letztes Jahr
    let yearShort = year.split("/").pop();

    return [moduleCode, yearShort, periodCode]
});

modules
"""

async def get_updates():
    updates = await bot.get_updates()
    for update in updates:
        print(update)


def show_result(module: module_type, old_dist: dist_type, new_dist: dist_type):
    xs = [mark["GRADETEXT"] for mark in new_dist]
    ys_old = [mark["COUNT"] for mark in old_dist]
    ys_new = [mark["COUNT"] for mark in new_dist]
    ys_diff = [new - old for old, new in zip(ys_old, ys_new)]

    # Tkinter setup
    root = tk.Tk()
    root.lift()
    root.attributes('-topmost', True)
    root.after(100, lambda: root.attributes('-topmost', False))
    root.focus_force()
    root.title(f"Neue Ergebnisse bei {MarkAlert.get_module_str(module)}")
    root.geometry("1000x800")

    ttk.Label(root, text=MarkAlert.get_module_str(module), font=("Arial", 14)).pack(pady=10)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(xs, ys_old, color="skyblue")
    ax.bar(xs, ys_diff, color="orange", bottom=ys_old)
    ax.set_title(
        f"Neue Ergebnisse bei {MarkAlert.get_module_str(module)}:\n{MarkAlert.get_new_marks(old_dist, new_dist)} Prüfungsverfahren geschlossen")
    ax.set_ylabel("Anzahl")

    def on_closing():
        root.quit()  # Stoppt die mainloop
        root.destroy()  # Zerstört das Fenster und alle Widgets

    # Diese Funktion an das Schließen-Ereignis des Fensters binden
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Embed chart in Tkinter
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    root.mainloop()


def save_result_image(module: module_type, old_dist: dist_type, new_dist: dist_type, filename: str = "result.png"):
    xs = [mark["GRADETEXT"] for mark in new_dist]
    ys_old = [mark["COUNT"] for mark in old_dist]
    ys_new = [mark["COUNT"] for mark in new_dist]
    ys_diff = [new - old for old, new in zip(ys_old, ys_new)]

    fig, ax = plt.subplots(figsize=(10, 8))  # größere Figur wie vorher
    ax.bar(xs, ys_old, color="skyblue", label="alt")
    ax.bar(xs, ys_diff, color="orange", bottom=ys_old, label="neu")
    ax.set_title(
        f"Neue Ergebnisse bei {MarkAlert.get_module_str(module)}:\n{MarkAlert.get_new_marks(old_dist, new_dist)} Prüfungsverfahren geschlossen")
    ax.set_ylabel("Anzahl")
    ax.set_xlabel("Noten")
    ax.legend()
    ax.grid(True, axis='y', linestyle='--', alpha=0.7)

    # Bild speichern
    fig.tight_layout()
    fig.savefig(filename, dpi=200)
    plt.close(fig)


def send_telegram(module: module_type, old_dist: dist_type, new_dist: dist_type):
    save_result_image(module, old_dist, new_dist, "result.png")

    async def send_group_photo():
        with open("result.png", "rb") as img:
            await bot.send_photo(
                chat_id=GROUP_CHAT_ID,
                photo=img,
                caption="Neue Prüfungsergebnisse!"
            )

    asyncio.run(send_group_photo())


if __name__ == '__main__':
    with open("modules.json", "r", encoding="utf-8") as f:
        modules = json.load(f)
    ma = MarkAlert(modules)

    # Only Desktop
    ma.add_callable(show_result)
    while True:
        ma.run()
        time.sleep(60)
