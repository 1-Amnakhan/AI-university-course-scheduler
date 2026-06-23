# gui.py
# Full Tkinter GUI for the University Course Scheduler
# Run this file instead of main.py when you want the interactive interface.

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import os

from data import load_courses, rooms, time_slots
from csp import build_csp
from solver import solve, nodes_explored
from visualize import build_dataframe, visualize_grid

#gui fix
import ctypes
import sys

# Fix blurry Tkinter UI on high-DPI displays (Windows)
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()   # Fallback
        except Exception:
            pass

# ── Color palette ─────────────────────────────────────────────────────────────
BG        = "#1e1e2e"
PANEL     = "#2a2a3e"
ACCENT    = "#7c6af7"
ACCENT2   = "#56cfb2"
TEXT      = "#e0e0f0"
SUBTEXT   = "#9090b0"
SUCCESS   = "#56cfb2"
ERROR     = "#f76a6a"
ROWEVEN   = "#252538"
ROWODD    = "#2a2a3e"
BTN_BG    = "#7c6af7"
BTN_FG    = "#ffffff"
BTN_HOV   = "#9a8cff"


class SchedulerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI University Course Scheduler")
        self.geometry("1100x750")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.csv_path = tk.StringVar(value="courses.csv (default)")
        self.status   = tk.StringVar(value="Ready — click Generate to build a schedule.")
        self.solution = None
        self.variables_meta = None
        self.df = None

        self._build_ui()

    # ── UI Construction ────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=ACCENT, pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🎓  AI University Course Scheduler",
                 font=("Segoe UI", 18, "bold"), bg=ACCENT, fg="white").pack()
        tk.Label(hdr, text="CSP · Backtracking · MRV Heuristic · Forward Checking",
                 font=("Segoe UI", 9), bg=ACCENT, fg="#d0ccff").pack()

        # ── Main body: left panel + right results ──────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        self._build_left_panel(body)
        self._build_right_panel(body)

        # ── Status bar ────────────────────────────────────────────────────────
        bar = tk.Frame(self, bg=PANEL, pady=5)
        bar.pack(fill="x", side="bottom")
        tk.Label(bar, textvariable=self.status, font=("Segoe UI", 9),
                 bg=PANEL, fg=SUBTEXT, anchor="w", padx=12).pack(fill="x")

    def _build_left_panel(self, parent):
        lf = tk.Frame(parent, bg=PANEL, width=260, padx=16, pady=16)
        lf.pack(side="left", fill="y", padx=(0, 12))
        lf.pack_propagate(False)

        # Section: Data source
        self._section(lf, "DATA SOURCE")
        tk.Label(lf, text="Courses CSV:", font=("Segoe UI", 9),
                 bg=PANEL, fg=SUBTEXT).pack(anchor="w")
        csv_row = tk.Frame(lf, bg=PANEL)
        csv_row.pack(fill="x", pady=(2, 8))
        tk.Entry(csv_row, textvariable=self.csv_path, font=("Segoe UI", 8),
                 bg="#1e1e2e", fg=TEXT, insertbackground=TEXT,
                 relief="flat", width=18).pack(side="left", fill="x", expand=True)
        self._btn(csv_row, "Browse", self._browse_csv, small=True).pack(side="right", padx=(4, 0))

        # Section: Configuration
        self._section(lf, "CONFIGURATION")

        tk.Label(lf, text="Rooms (comma-separated):", font=("Segoe UI", 9),
                 bg=PANEL, fg=SUBTEXT).pack(anchor="w")
        self.rooms_var = tk.StringVar(value=", ".join(rooms))
        tk.Entry(lf, textvariable=self.rooms_var, font=("Segoe UI", 8),
                 bg="#1e1e2e", fg=TEXT, insertbackground=TEXT,
                 relief="flat").pack(fill="x", pady=(2, 8))

        tk.Label(lf, text="Max sessions/day per course:", font=("Segoe UI", 9),
                 bg=PANEL, fg=SUBTEXT).pack(anchor="w")
        self.maxsess_var = tk.IntVar(value=1)
        ttk.Spinbox(lf, from_=1, to=4, textvariable=self.maxsess_var,
                    width=6, font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 8))

        # Section: Actions
        self._section(lf, "ACTIONS")
        self._btn(lf, "⚡  Generate Schedule", self._run_solver).pack(fill="x", pady=(0, 6))
        self._btn(lf, "📊  View Timetable Grid", self._show_grid, color=ACCENT2).pack(fill="x", pady=(0, 6))
        self._btn(lf, "💾  Export CSV", self._export_csv, color="#4a9eff").pack(fill="x", pady=(0, 6))
        self._btn(lf, "🔄  Reset", self._reset, color="#888").pack(fill="x")

        # Section: Stats
        self._section(lf, "STATISTICS")
        self.stats_frame = tk.Frame(lf, bg=PANEL)
        self.stats_frame.pack(fill="x")
        self._stat_row(self.stats_frame, "Sessions:", "—", "lbl_sessions")
        self._stat_row(self.stats_frame, "Nodes explored:", "—", "lbl_nodes")
        self._stat_row(self.stats_frame, "Solve time:", "—", "lbl_time")
        self._stat_row(self.stats_frame, "Violations:", "—", "lbl_violations")

    def _build_right_panel(self, parent):
        rf = tk.Frame(parent, bg=BG)
        rf.pack(side="left", fill="both", expand=True)

        # Tabs
        self.notebook = ttk.Notebook(rf)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=TEXT,
                        padding=[12, 6], font=("Segoe UI", 9))
        style.map("TNotebook.Tab", background=[("selected", ACCENT)],
                  foreground=[("selected", "white")])
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Timetable table
        self.tab_table = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tab_table, text="  📋  Timetable  ")
        self._build_table_tab(self.tab_table)

        # Tab 2: Courses loaded
        self.tab_courses = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tab_courses, text="  📚  Courses Loaded  ")
        self._build_courses_tab(self.tab_courses)

        # Tab 3: Log
        self.tab_log = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tab_log, text="  🖥  Log  ")
        self._build_log_tab(self.tab_log)

    def _build_table_tab(self, parent):
        cols = ("Session", "Course", "Teacher", "Day", "Time", "Room")
        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="both", expand=True, pady=8)

        style = ttk.Style()
        style.configure("Treeview", background=ROWEVEN, foreground=TEXT,
                        fieldbackground=ROWEVEN, rowheight=26,
                        font=("Segoe UI", 9), borderwidth=0)
        style.configure("Treeview.Heading", background=PANEL, foreground=ACCENT,
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", ACCENT)])

        self.tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
        col_widths = [80, 220, 130, 55, 65, 80]
        for col, w in zip(cols, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.tag_configure("odd",  background=ROWODD)
        self.tree.tag_configure("even", background=ROWEVEN)

        # Placeholder
        self.tree.insert("", "end", values=("—", "Run the scheduler to see results", "", "", "", ""))

    def _build_courses_tab(self, parent):
        cols = ("ID", "Course Name", "Teacher", "Sessions/Week")
        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="both", expand=True, pady=8)

        self.course_tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
        widths = [60, 240, 150, 100]
        for col, w in zip(cols, widths):
            self.course_tree.heading(col, text=col)
            self.course_tree.column(col, width=w, anchor="center")

        vsb2 = ttk.Scrollbar(frame, orient="vertical", command=self.course_tree.yview)
        self.course_tree.configure(yscrollcommand=vsb2.set)
        self.course_tree.pack(side="left", fill="both", expand=True)
        vsb2.pack(side="right", fill="y")

        self.course_tree.tag_configure("odd",  background=ROWODD)
        self.course_tree.tag_configure("even", background=ROWEVEN)
        self._refresh_courses_tab()

    def _build_log_tab(self, parent):
        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(frame, bg="#13131f", fg=SUBTEXT,
                                font=("Consolas", 9), relief="flat",
                                state="disabled", wrap="word")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=vsb.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._log("Scheduler ready. Load a CSV or use default data and click Generate.\n")

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _section(self, parent, text):
        tk.Label(parent, text=text, font=("Segoe UI", 8, "bold"),
                 bg=PANEL, fg=ACCENT).pack(anchor="w", pady=(12, 2))
        tk.Frame(parent, bg=ACCENT, height=1).pack(fill="x", pady=(0, 6))

    def _btn(self, parent, text, cmd, color=None, small=False):
        c = color or BTN_BG
        font = ("Segoe UI", 8) if small else ("Segoe UI", 10, "bold")
        pady = 3 if small else 8
        b = tk.Button(parent, text=text, command=cmd, bg=c, fg=BTN_FG,
                      font=font, relief="flat", cursor="hand2",
                      activebackground=BTN_HOV, activeforeground="white",
                      pady=pady, bd=0)
        b.bind("<Enter>", lambda e: b.config(bg=BTN_HOV))
        b.bind("<Leave>", lambda e: b.config(bg=c))
        return b

    def _stat_row(self, parent, label, value, attr):
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", pady=1)
        tk.Label(row, text=label, font=("Segoe UI", 8), bg=PANEL, fg=SUBTEXT,
                 width=16, anchor="w").pack(side="left")
        lbl = tk.Label(row, text=value, font=("Segoe UI", 8, "bold"),
                       bg=PANEL, fg=ACCENT2)
        lbl.pack(side="left")
        setattr(self, attr, lbl)

    def _log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _set_status(self, msg, color=None):
        self.status.set(msg)

    # ── Actions ────────────────────────────────────────────────────────────────
    def _browse_csv(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            self.csv_path.set(path)
            self._refresh_courses_tab(path)
            self._log(f"[CSV] Loaded: {path}\n")

    def _refresh_courses_tab(self, csv_path=None):
        for item in self.course_tree.get_children():
            self.course_tree.delete(item)
        try:
            courses = load_courses(csv_path)
            for i, c in enumerate(courses):
                tag = "even" if i % 2 == 0 else "odd"
                self.course_tree.insert("", "end", tag=tag, values=(
                    c["id"], c["name"],
                    c["teacher"].replace("_", " "),
                    c["sessions_per_week"]
                ))
        except Exception as e:
            self._log(f"[ERROR] Could not load courses: {e}\n")

    def _run_solver(self):
        """Run solver in a background thread so the UI stays responsive."""
        self._btn_generate_state("disabled")
        self._set_status("⏳ Solving — please wait...")
        self._log("\n" + "="*55 + "\n")
        self._log("[*] Starting CSP solver...\n")
        thread = threading.Thread(target=self._solve_worker, daemon=True)
        thread.start()

    def _solve_worker(self):
        try:
            # Load data
            csv_val = self.csv_path.get()
            csv_file = None if "default" in csv_val else csv_val
            courses = load_courses(csv_file)

            r_raw = self.rooms_var.get()
            r_list = [r.strip() for r in r_raw.split(",") if r.strip()]

            self._log(f"[*] Courses: {len(courses)}  |  Rooms: {len(r_list)}  |  Slots: {len(time_slots)}\n")

            variables, domains, variables_meta = build_csp(courses, r_list, time_slots)
            total = len(variables)
            self._log(f"[*] Variables (sessions): {total}\n")
            self._log(f"[*] Running Backtracking + MRV + Forward Checking...\n")

            t0 = time.time()
            solution, n_nodes = solve(variables, domains, variables_meta)
            elapsed = time.time() - t0

            if solution is None:
                self.after(0, self._on_no_solution)
                return

            # Verify
            violations = self._verify(solution, variables_meta)
            self.solution = solution
            self.variables_meta = variables_meta
            self.df = build_dataframe(solution, variables_meta)

            self.after(0, lambda: self._on_solution_found(
                total, n_nodes, elapsed, violations))

        except Exception as e:
            self.after(0, lambda: self._on_error(str(e)))

    def _verify(self, solution, variables_meta):
        violations = []
        items = list(solution.items())
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                va, (ta, ra) = items[i]
                vb, (tb, rb) = items[j]
                if ta != tb:
                    continue
                ca = variables_meta[va]
                cb = variables_meta[vb]
                if ra == rb:
                    violations.append(f"ROOM CLASH: {va} & {vb} in {ra} at {ta}")
                if ca["teacher"] == cb["teacher"]:
                    violations.append(f"TEACHER CLASH: {ca['teacher']} at {ta}")
                if ca["id"] == cb["id"]:
                    violations.append(f"COURSE CLASH: {ca['id']} at {ta}")
        return violations

    def _on_solution_found(self, total, nodes, elapsed, violations):
        # Update stats panel
        self.lbl_sessions.config(text=f"{total}", fg=ACCENT2)
        self.lbl_nodes.config(text=f"{nodes}", fg=ACCENT2)
        self.lbl_time.config(text=f"{elapsed:.4f}s", fg=ACCENT2)
        v_color = ERROR if violations else SUCCESS
        v_text  = f"{len(violations)} ❌" if violations else "0 ✓"
        self.lbl_violations.config(text=v_text, fg=v_color)

        # Log
        self._log(f"[✓] Solved in {elapsed:.4f}s  |  Nodes: {nodes}\n")
        if violations:
            for v in violations:
                self._log(f"    ⚠ {v}\n")
        else:
            self._log("[✓] All constraints satisfied — conflict-free schedule!\n")

        # Populate table
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, row in self.df.iterrows():
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", tag=tag, values=(
                row["Session"], row["Course"], row["Teacher"],
                row["Day"], row["Time"], row["Room"]
            ))

        self.notebook.select(self.tab_table)
        self._set_status(f"✅ Schedule generated — {total} sessions, 0 violations, {elapsed:.4f}s")
        self._btn_generate_state("normal")

    def _on_no_solution(self):
        self._log("[!] NO SOLUTION FOUND.\n")
        self._log("    → Add more rooms or time slots in data.py to relax constraints.\n")
        self._set_status("❌ No solution found — try adding more rooms or time slots.")
        messagebox.showerror("No Solution",
            "The scheduler could not find a valid timetable.\n\n"
            "Try:\n• Adding more rooms\n• Adding more time slots\n• Reducing sessions_per_week")
        self._btn_generate_state("normal")

    def _on_error(self, msg):
        self._log(f"[ERROR] {msg}\n")
        self._set_status(f"Error: {msg}")
        messagebox.showerror("Error", msg)
        self._btn_generate_state("normal")

    def _show_grid(self):
        if self.solution is None:
            messagebox.showwarning("No Schedule", "Generate a schedule first.")
            return
        r_list = [r.strip() for r in self.rooms_var.get().split(",") if r.strip()]
        self._log("[*] Opening timetable grid window...\n")
        visualize_grid(self.solution, self.variables_meta, time_slots, r_list)

    def _export_csv(self):
        if self.df is None:
            messagebox.showwarning("No Schedule", "Generate a schedule first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="timetable_output.csv")
        if path:
            self.df.to_csv(path, index=False)
            self._log(f"[+] Exported to: {path}\n")
            self._set_status(f"Saved: {path}")
            messagebox.showinfo("Exported", f"Timetable saved to:\n{path}")

    def _reset(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree.insert("", "end", values=("—", "Run the scheduler to see results", "", "", "", ""))
        self.solution = None
        self.df = None
        for attr in ("lbl_sessions", "lbl_nodes", "lbl_time", "lbl_violations"):
            getattr(self, attr).config(text="—", fg=ACCENT2)
        self._set_status("Reset. Click Generate to build a new schedule.")
        self._log("[*] Reset.\n")

    def _btn_generate_state(self, state):
        pass  # threading handles responsiveness


if __name__ == "__main__":
    app = SchedulerApp()
    app.mainloop()
