"""PDF vers PPT - interface graphique (Mac / Windows)."""
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from converter import convert

APP_NAME = "PDF vers PPT"
QUALITES = {
    "Haute (300 dpi)": 300,
    "Très haute (400 dpi)": 400,
    "Maximale (600 dpi)": 600,
    "Standard (200 dpi)": 200,
}
FORMATS = {
    "PNG (sans perte, fichier plus lourd)": "png",
    "JPEG qualité 95 (fichier plus léger)": "jpeg",
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("560x400")
        self.minsize(480, 360)
        self.files = []
        self.cancel_flag = False
        self.working = False

        pad = {"padx": 12, "pady": 6}
        ttk.Label(self, text=APP_NAME, font=("Helvetica", 18, "bold")).pack(**pad)
        ttk.Label(self, text="Chaque page du PDF devient une diapositive image, "
                             "sans aucune modification du contenu.",
                  wraplength=520).pack(**pad)

        ttk.Button(self, text="Choisir un ou plusieurs PDF…",
                   command=self.choose).pack(**pad)
        self.files_var = tk.StringVar(value="Aucun fichier sélectionné")
        ttk.Label(self, textvariable=self.files_var, wraplength=520,
                  foreground="#555").pack(**pad)

        opts = ttk.Frame(self)
        opts.pack(**pad)
        ttk.Label(opts, text="Qualité :").grid(row=0, column=0, sticky="e")
        self.q = ttk.Combobox(opts, values=list(QUALITES), state="readonly", width=32)
        self.q.current(0)
        self.q.grid(row=0, column=1, padx=6, pady=3)
        ttk.Label(opts, text="Format image :").grid(row=1, column=0, sticky="e")
        self.f = ttk.Combobox(opts, values=list(FORMATS), state="readonly", width=32)
        self.f.current(0)
        self.f.grid(row=1, column=1, padx=6, pady=3)

        self.go = ttk.Button(self, text="Convertir en PowerPoint", command=self.start)
        self.go.pack(**pad)
        self.bar = ttk.Progressbar(self, length=480, mode="determinate")
        self.bar.pack(**pad)
        self.status = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.status).pack(**pad)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def choose(self):
        if self.working:
            return
        paths = filedialog.askopenfilenames(
            title="Choisir des PDF", filetypes=[("PDF", "*.pdf *.PDF")])
        if paths:
            self.files = list(paths)
            names = [os.path.basename(p) for p in self.files]
            txt = ", ".join(names[:3]) + (f" (+{len(names) - 3})" if len(names) > 3 else "")
            self.files_var.set(f"{len(names)} fichier(s) : {txt}")

    def start(self):
        if self.working:
            self.cancel_flag = True
            self.status.set("Annulation…")
            return
        if not self.files:
            messagebox.showinfo(APP_NAME, "Choisissez d'abord un fichier PDF.")
            return
        outdir = None
        if len(self.files) == 1:
            out = filedialog.asksaveasfilename(
                title="Enregistrer le PowerPoint",
                defaultextension=".pptx",
                initialdir=os.path.dirname(self.files[0]),
                initialfile=os.path.splitext(os.path.basename(self.files[0]))[0] + ".pptx",
                filetypes=[("PowerPoint", "*.pptx")])
            if not out:
                return
            jobs = [(self.files[0], out)]
        else:
            outdir = filedialog.askdirectory(
                title="Dossier où enregistrer les PowerPoint",
                initialdir=os.path.dirname(self.files[0]))
            if not outdir:
                return
            jobs = [(p, os.path.join(outdir, os.path.splitext(os.path.basename(p))[0] + ".pptx"))
                    for p in self.files]

        self.working = True
        self.cancel_flag = False
        self.go.config(text="Annuler")
        dpi = QUALITES[self.q.get()]
        fmt = FORMATS[self.f.get()]
        threading.Thread(target=self.run, args=(jobs, dpi, fmt), daemon=True).start()

    def run(self, jobs, dpi, fmt):
        done, errors = [], []
        for n, (src, dst) in enumerate(jobs, 1):
            name = os.path.basename(src)

            def prog(i, total, n=n, name=name):
                self.after(0, self.update_progress, i, total,
                           f"Fichier {n}/{len(jobs)} - {name} : page {i}/{total}")
            try:
                convert(src, dst, dpi=dpi, image_format=fmt, progress=prog,
                        cancel=lambda: self.cancel_flag)
                done.append(dst)
            except InterruptedError:
                break
            except Exception as e:  # noqa: BLE001
                errors.append(f"{name} : {e}")
        self.after(0, self.finish, done, errors)

    def update_progress(self, i, total, text):
        self.bar["maximum"] = total
        self.bar["value"] = i
        self.status.set(text)

    def finish(self, done, errors):
        self.working = False
        self.go.config(text="Convertir en PowerPoint")
        if self.cancel_flag:
            self.status.set("Conversion annulée.")
            return
        self.status.set(f"Terminé : {len(done)} fichier(s) créé(s).")
        msg = ""
        if done:
            msg += "PowerPoint créé(s) :\n" + "\n".join(done)
        if errors:
            msg += "\n\nErreurs :\n" + "\n".join(errors)
        (messagebox.showwarning if errors else messagebox.showinfo)(APP_NAME, msg)
        if done and not errors:
            reveal(done[0])

    def on_close(self):
        self.cancel_flag = True
        self.destroy()


def reveal(path):
    try:
        if sys.platform == "darwin":
            os.system(f'open -R "{path}"')
        elif os.name == "nt":
            os.system(f'explorer /select,"{os.path.normpath(path)}"')
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    # Mode ligne de commande : app.py fichier.pdf [sortie.pptx]
    if len(sys.argv) > 1 and sys.argv[1].lower().endswith(".pdf"):
        out = convert(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
        print(out)
    else:
        App().mainloop()
