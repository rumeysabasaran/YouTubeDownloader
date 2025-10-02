
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pytubefix
import os


class YouTubeDownloader:
    """High-level wrapper around pytubefix for downloading a single video."""

    def __init__(self):
        self._last_percent = 0

    def _on_progress(self, on_progress_ui, stream, chunk, bytes_remaining):
        try:
            total_size = stream.filesize
            bytes_downloaded = total_size - bytes_remaining
            percent = int(bytes_downloaded / total_size * 100)
        except Exception:
            percent = 0
        self._last_percent = percent
        # Schedule UI update on main thread
        if on_progress_ui is not None:
            on_progress_ui(percent)

    def download_highest(self, url: str, output_path: str | None, on_progress_ui=None) -> str:
        """
        Download the highest resolution stream for a YouTube video.

        Returns the final file path on success. Raises exceptions on failure.
        """
        yt = pytubefix.YouTube(url)
        yt.register_on_progress_callback(lambda s, c, r: self._on_progress(on_progress_ui, s, c, r))
        stream = yt.streams.get_highest_resolution()
        file_path = stream.download(output_path or "")
        return file_path


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("520x230")
        self.root.resizable(False, False)

        self.downloader = YouTubeDownloader()

        # State
        self.url_var = tk.StringVar()
        self.path_var = tk.StringVar(value="")
        self.progress_var = tk.IntVar(value=0)
        self.status_var = tk.StringVar(value="Hazır")

        # UI
        self._build_ui()

    def _build_ui(self):
        padding = {"padx": 12, "pady": 8}

        url_label = ttk.Label(self.root, text="Video URL")
        url_label.grid(row=0, column=0, sticky="w", **padding)
        url_entry = ttk.Entry(self.root, textvariable=self.url_var, width=52)
        url_entry.grid(row=0, column=1, columnspan=2, sticky="we", **padding)

        path_label = ttk.Label(self.root, text="Kayıt Klasörü")
        path_label.grid(row=1, column=0, sticky="w", **padding)
        path_entry = ttk.Entry(self.root, textvariable=self.path_var, width=41)
        path_entry.grid(row=1, column=1, sticky="we", **padding)
        browse_btn = ttk.Button(self.root, text="Seç...", command=self._choose_folder)
        browse_btn.grid(row=1, column=2, sticky="e", **padding)

        self.progress = ttk.Progressbar(self.root, orient="horizontal", mode="determinate", maximum=100, variable=self.progress_var, length=460)
        self.progress.grid(row=2, column=0, columnspan=3, sticky="we", **padding)

        self.status_label = ttk.Label(self.root, textvariable=self.status_var)
        self.status_label.grid(row=3, column=0, columnspan=3, sticky="w", **padding)

        self.download_btn = ttk.Button(self.root, text="İndir", command=self._start_download)
        self.download_btn.grid(row=4, column=2, sticky="e", **padding)

        # allow column 1 to stretch if window is resized
        self.root.grid_columnconfigure(1, weight=1)

    def _choose_folder(self):
        folder = filedialog.askdirectory(title="Kayıt klasörünü seç")
        if folder:
            self.path_var.set(folder)

    def _set_busy(self, busy: bool):
        state = tk.DISABLED if busy else tk.NORMAL
        self.download_btn.configure(state=state)

    def _start_download(self):
        url = self.url_var.get().strip()
        path = self.path_var.get().strip()

        if not url:
            messagebox.showwarning("Uyarı", "Lütfen bir YouTube URL'si girin.")
            return

        if path and not os.path.isdir(path):
            messagebox.showwarning("Uyarı", "Geçerli bir klasör seçin veya boş bırakın.")
            return

        self.progress_var.set(0)
        self.status_var.set("⬇️ İndiriliyor... %0")
        self._set_busy(True)

        def on_progress_ui(percent: int):
            # Ensure UI updates happen on the main thread
            self.root.after(0, lambda: self._update_progress(percent))

        def worker():
            try:
                file_path = self.downloader.download_highest(url, path or None, on_progress_ui)
                self.root.after(0, lambda: self._finish_success(file_path))
            except Exception as exc:
                self.root.after(0, lambda: self._finish_error(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _update_progress(self, percent: int):
        self.progress_var.set(max(0, min(100, int(percent))))
        self.status_var.set(f"⬇️ İndiriliyor... %{self.progress_var.get()}")

    def _finish_success(self, file_path: str):
        self._set_busy(False)
        self.progress_var.set(100)
        self.status_var.set("✅ İndirme tamamlandı")
        messagebox.showinfo("Tamamlandı", f"Video indirildi:\n{file_path}")

    def _finish_error(self, exc: Exception):
        self._set_busy(False)
        self.status_var.set("❌ Hata oluştu")
        messagebox.showerror("Hata", f"İndirme başarısız:\n{exc}")

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
