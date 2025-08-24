# Bank Management System - Multi-Panel GUI (Tkinter)
# Final Stable Version with Custom Dialogs + Background + Optimizations
# Author: ChatGPT

import json
import random
import string
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except Exception:
    PIL_OK = False


#############################
# Data Layer
#############################
class DataStore:
    DB_FILE = 'data.json'

    def __init__(self):
        self.data = {
            "accounts": [],
            "staff": [],
            "manager": {"id": "admin", "password": "1234"}
        }
        self._load_or_init()

    def _load_or_init(self):
        if Path(self.DB_FILE).exists():
            try:
                with open(self.DB_FILE, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                if isinstance(raw, list):
                    self.data["accounts"] = raw
                elif isinstance(raw, dict):
                    # merge keys
                    for k in ["accounts", "staff", "manager"]:
                        if k in raw:
                            self.data[k] = raw[k]
                self._save()
            except Exception:
                self._save()
        else:
            self._save()

    def _save(self):
        with open(self.DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    @staticmethod
    def _gen_account_no():
        alpha = ''.join(random.choices(string.ascii_uppercase, k=3))
        num = ''.join(random.choices(string.digits, k=3))
        return f"{alpha}{num}"

    def _normalize_accno(self, acc):
        return acc.get("accountNo") or acc.get("accountNo.")  # legacy key support

    def _find_account(self, *, acc_no=None, pin=None, name=None):
        res = []
        for acc in self.data["accounts"]:
            accno = self._normalize_accno(acc)
            ok = True
            if acc_no is not None and accno != acc_no:
                ok = False
            if pin is not None and acc.get("pin") != pin:
                ok = False
            if name is not None and name.lower() not in acc.get("name", "").lower():
                ok = False
            if ok:
                res.append(acc)
        return res

    def create_account(self, name, age, email, pin):
        if not name or not email:
            raise ValueError("Name/Email required")
        age = int(age)
        pin = int(pin)
        if age < 18:
            raise ValueError("Age must be 18+")
        if len(str(pin)) != 4:
            raise ValueError("PIN must be 4 digits")
        acc_no = self._gen_account_no()
        acc = {"name": name, "age": age, "email": email, "pin": pin, "accountNo": acc_no, "balance": 0}
        self.data["accounts"].append(acc)
        self._save()
        return acc

    def update_account(self, acc_no, **fields):
        accs = self._find_account(acc_no=acc_no)
        if not accs:
            raise ValueError("Account not found")
        acc = accs[0]
        for k, v in fields.items():
            if v is None or v == '':
                continue
            if k == "pin":
                v = int(v)
                if len(str(v)) != 4:
                    raise ValueError("PIN must be 4 digits")
            if k == "age":
                v = int(v)
                if v < 18:
                    raise ValueError("Age must be 18+")
            if k in ["balance"]:
                v = int(v)
            acc[k] = v
        self._save()
        return acc

    def delete_account(self, acc_no):
        accs = self._find_account(acc_no=acc_no)
        if not accs:
            raise ValueError("Account not found")
        self.data["accounts"].remove(accs[0])
        self._save()

    def deposit(self, acc_no, pin, amount):
        amount = int(amount)
        if amount <= 0:
            raise ValueError("Invalid amount")
        accs = self._find_account(acc_no=acc_no, pin=int(pin))
        if not accs:
            raise ValueError("Invalid account or PIN")
        accs[0]["balance"] += amount
        self._save()
        return accs[0]["balance"]

    def withdraw(self, acc_no, pin, amount):
        amount = int(amount)
        accs = self._find_account(acc_no=acc_no, pin=int(pin))
        if not accs:
            raise ValueError("Invalid account or PIN")
        if amount <= 0 or accs[0]["balance"] < amount:
            raise ValueError("Insufficient balance")
        accs[0]["balance"] -= amount
        self._save()
        return accs[0]["balance"]

    def search(self, *, name=None, acc_no=None):
        return self._find_account(name=name, acc_no=acc_no)

    def add_staff(self, staff_id, password, name):
        if any(s["id"] == staff_id for s in self.data["staff"]):
            raise ValueError("Staff already exists")
        self.data["staff"].append({"id": staff_id, "password": password, "name": name})
        self._save()

    def edit_staff(self, staff_id, new_name=None, new_password=None):
        for s in self.data["staff"]:
            if s["id"] == staff_id:
                if new_name:
                    s["name"] = new_name
                if new_password:
                    s["password"] = new_password
                self._save()
                return
        raise ValueError("Staff not found")

    def remove_staff(self, staff_id):
        for s in self.data["staff"]:
            if s["id"] == staff_id:
                self.data["staff"].remove(s)
                self._save()
                return
        raise ValueError("Staff not found")

    def check_manager_login(self, uid, pwd):
        return uid == self.data["manager"]["id"] and pwd == self.data["manager"]["password"]

    def check_staff_login(self, uid, pwd):
        return any(s["id"] == uid and s["password"] == pwd for s in self.data["staff"])

    def get_user_details(self, acc_no, pin):
        accs = self._find_account(acc_no=acc_no, pin=int(pin))
        return accs[0] if accs else None

    def reset_pin(self, acc_no, old_pin, new_pin):
        accs = self._find_account(acc_no=acc_no, pin=int(old_pin))
        if not accs:
            raise ValueError("Invalid account or old PIN")
        if len(str(new_pin)) != 4:
            raise ValueError("PIN must be 4 digits")
        accs[0]["pin"] = int(new_pin)
        self._save()


#############################
# Reusable Multi-field Dialog
#############################
class FormDialog(tk.Toplevel):
    """
    fields: list of dicts like:
      {"label": "Name", "key": "name", "type": "text"|"int"|"password", "initial": ""}
    """
    def __init__(self, parent, title, fields, submit_text="Submit"):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()  # modal
        self.result = None
        self.inputs = {}

        body = ttk.Frame(self)
        body.pack(padx=14, pady=12, fill="both", expand=True)

        for i, fld in enumerate(fields):
            ttk.Label(body, text=fld["label"]).grid(row=i, column=0, sticky="w", padx=6, pady=6)
            show = "*" if fld.get("type") == "password" else ""
            ent = ttk.Entry(body, show=show)
            ent.grid(row=i, column=1, padx=6, pady=6)
            if fld.get("initial") not in (None, ""):
                ent.insert(0, str(fld["initial"]))
            self.inputs[fld["key"]] = (ent, fld.get("type", "text"))

        btns = ttk.Frame(self)
        btns.pack(pady=(0, 10))
        ttk.Button(btns, text=submit_text, command=self._on_submit).pack(side="left", padx=5)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="left", padx=5)

        self.bind("<Return>", lambda e: self._on_submit())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.after(50, self._focus_first)

    def _focus_first(self):
        # focus first entry
        if self.inputs:
            first_key = list(self.inputs.keys())[0]
            self.inputs[first_key][0].focus_set()

    def _on_submit(self):
        vals = {}
        try:
            for key, (entry, typ) in self.inputs.items():
                v = entry.get()
                if typ == "int" and v != "":
                    v = int(v)
                vals[key] = v
            self.result = vals
            self.destroy()
        except ValueError:
            messagebox.showerror("Invalid", "Please enter valid numeric values where required.")


#############################
# GUI App
#############################
class App(tk.Tk):
    def __init__(self, store: DataStore):
        super().__init__()
        self.title("Bank Management System")
        self.geometry("1100x700")
        self.store = store

        # Background
        self._bg_img = None
        self._bg_label = tk.Label(self)
        self._bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._set_background("bg.jpg")

        # Container (opaque so text visible)
        self.container = tk.Frame(self, bg="#ffffff", bd=0, highlightthickness=0)
        self.container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.96, relheight=0.92)

        self.frames = {}
        for F in (LoginFrame, ManagerFrame, StaffFrame, UserFrame):
            frame = F(parent=self.container, controller=self)
            self.frames[F.__name__] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_frame("LoginFrame")

    def _set_background(self, path):
        if PIL_OK and Path(path).exists():
            try:
                # cache scaled image
                img = Image.open(path)
                img = img.resize((1100, 700))
                self._bg_img = ImageTk.PhotoImage(img)
                self._bg_label.configure(image=self._bg_img)
            except Exception:
                self.configure(bg="#1e293b")
        else:
            self.configure(bg="#1e293b")

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()


#############################
# Frames
#############################
class LoginFrame(ttk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller

        title = ttk.Label(self, text="Login", font=("Arial", 22, "bold"))
        title.pack(pady=16)

        self.role = tk.StringVar(value="Manager")
        row = ttk.Frame(self); row.pack(pady=6)
        ttk.Label(row, text="Role:").pack(side="left", padx=6)
        self.role_cb = ttk.Combobox(row, textvariable=self.role, values=["Manager", "Staff", "User"], state='readonly', width=20)
        self.role_cb.pack(side="left", padx=6)

        self.id_entry = ttk.Entry(self, width=30)
        self.pwd_entry = ttk.Entry(self, show='*', width=30)
        self.acc_entry = ttk.Entry(self, width=30)
        self.pin_entry = ttk.Entry(self, show='*', width=30)

        self.fields_wrap = ttk.Frame(self); self.fields_wrap.pack(pady=10)
        ttk.Button(self, text="Login", command=self.login).pack(pady=10)

        self.role_cb.bind('<<ComboboxSelected>>', lambda e: self.render_fields())
        self.render_fields()

    def render_fields(self):
        for w in self.fields_wrap.winfo_children():
            w.destroy()

        if self.role.get() in ("Manager", "Staff"):
            r1 = ttk.Frame(self.fields_wrap); r1.pack(pady=4)
            ttk.Label(r1, text="ID: ").pack(side="left")
            self.id_entry = ttk.Entry(r1, width=25)   # <-- parent सही set
            self.id_entry.pack(side="left", padx=6)

            r2 = ttk.Frame(self.fields_wrap); r2.pack(pady=4)
            ttk.Label(r2, text="Password: ").pack(side="left")
            self.pwd_entry = ttk.Entry(r2, show='*', width=25)
            self.pwd_entry.pack(side="left", padx=6)

        else:  # User login
            r1 = ttk.Frame(self.fields_wrap); r1.pack(pady=4)
            ttk.Label(r1, text="Account No: ").pack(side="left")
            self.acc_entry = ttk.Entry(r1, width=25)
            self.acc_entry.pack(side="left", padx=6)

            r2 = ttk.Frame(self.fields_wrap); r2.pack(pady=4)
            ttk.Label(r2, text="PIN: ").pack(side="left")
            self.pin_entry = ttk.Entry(r2, show='*', width=25)
            self.pin_entry.pack(side="left", padx=6)

    def login(self):
        ds = self.controller.store
        if self.role.get() == "Manager":
            if ds.check_manager_login(self.id_entry.get(), self.pwd_entry.get()):
                self.controller.show_frame("ManagerFrame")
            else:
                messagebox.showerror("Error", "Invalid Manager login")
        elif self.role.get() == "Staff":
            if ds.check_staff_login(self.id_entry.get(), self.pwd_entry.get()):
                self.controller.show_frame("StaffFrame")
            else:
                messagebox.showerror("Error", "Invalid Staff login")
        else:
            acc = self.acc_entry.get().strip()
            pin = self.pin_entry.get().strip()
            if not pin.isdigit():
                messagebox.showerror("Error", "Enter numeric PIN")
                return
            details = ds.get_user_details(acc, int(pin))
            if details:
                frame: UserFrame = self.controller.frames["UserFrame"]
                frame.current_user = details
                self.controller.show_frame("UserFrame")
            else:
                messagebox.showerror("Error", "Invalid User login")


class ManagerFrame(ttk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller

        top = ttk.Frame(self); top.pack(fill="x", pady=8)
        ttk.Label(top, text="Manager Panel", font=("Arial", 20, "bold")).pack(side="left", padx=8)
        ttk.Button(top, text="Logout", command=lambda: controller.show_frame("LoginFrame")).pack(side="right", padx=8)

        # search bar
        sb = ttk.Frame(self); sb.pack(fill="x", pady=4)
        self.search_txt = tk.StringVar()
        ttk.Entry(sb, textvariable=self.search_txt, width=30).pack(side="left", padx=6)
        ttk.Button(sb, text="Search by Name", command=self.search_name).pack(side="left", padx=4)
        ttk.Button(sb, text="Search by Account", command=self.search_acc).pack(side="left", padx=4)
        ttk.Button(sb, text="Show All", command=self.refresh).pack(side="left", padx=4)

        # table
        cols = ("Name", "Age", "Email", "AccountNo", "PIN", "Balance")
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=16)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=150 if c != "Email" else 220, anchor="center")
        self.tree.pack(fill='both', expand=True, padx=8, pady=6)

        # action buttons
        btns = ttk.Frame(self); btns.pack(pady=6)
        ttk.Button(btns, text="Create Account", command=self.create_account).pack(side='left', padx=5)
        ttk.Button(btns, text="Update Selected", command=self.update_selected).pack(side='left', padx=5)
        ttk.Button(btns, text="Delete Selected", command=self.delete_selected).pack(side='left', padx=5)
        ttk.Separator(btns, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(btns, text="Add Staff", command=self.add_staff).pack(side='left', padx=5)
        ttk.Button(btns, text="Edit Staff", command=self.edit_staff).pack(side='left', padx=5)
        ttk.Button(btns, text="Remove Staff", command=self.remove_staff).pack(side='left', padx=5)

    def on_show(self):
        self.refresh()

    def _fill_table(self, accounts):
        self.tree.delete(*self.tree.get_children())
        for acc in accounts:
            accno = acc.get("accountNo") or acc.get("accountNo.")
            self.tree.insert('', 'end', values=(acc['name'], acc['age'], acc['email'], accno, acc['pin'], acc['balance']))

    def refresh(self):
        self._fill_table(self.controller.store.data["accounts"])

    def search_name(self):
        q = self.search_txt.get().strip()
        self._fill_table(self.controller.store.search(name=q) if q else self.controller.store.data["accounts"])

    def search_acc(self):
        q = self.search_txt.get().strip()
        self._fill_table(self.controller.store.search(acc_no=q) if q else self.controller.store.data["accounts"])

    def create_account(self):
        d = FormDialog(self, "Create Account", [
            {"label": "Name", "key": "name", "type": "text"},
            {"label": "Age", "key": "age", "type": "int"},
            {"label": "Email", "key": "email", "type": "text"},
            {"label": "PIN (4-digit)", "key": "pin", "type": "int"},
        ], submit_text="Create")
        self.wait_window(d)
        if d.result:
            try:
                self.controller.store.create_account(d.result["name"], d.result["age"], d.result["email"], d.result["pin"])
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _selected_accno(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a row first.")
            return None
        vals = self.tree.item(sel[0], "values")
        return vals[3]  # AccountNo

    def update_selected(self):
        accno = self._selected_accno()
        if not accno:
            return
        d = FormDialog(self, f"Update Account {accno}", [
            {"label": "Name", "key": "name", "type": "text"},
            {"label": "Age", "key": "age", "type": "int"},
            {"label": "Email", "key": "email", "type": "text"},
            {"label": "PIN (4-digit)", "key": "pin", "type": "int"},
            {"label": "Balance (optional)", "key": "balance", "type": "int"},
        ], submit_text="Update")
        self.wait_window(d)
        if d.result:
            try:
                self.controller.store.update_account(accno, **{k: v for k, v in d.result.items() if v != ""})
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def delete_selected(self):
        accno = self._selected_accno()
        if not accno:
            return
        if messagebox.askyesno("Confirm", f"Delete account {accno}?"):
            try:
                self.controller.store.delete_account(accno)
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # Staff management
    def add_staff(self):
        d = FormDialog(self, "Add Staff", [
            {"label": "Staff ID", "key": "sid", "type": "text"},
            {"label": "Password", "key": "pwd", "type": "password"},
            {"label": "Name", "key": "name", "type": "text"},
        ], submit_text="Add")
        self.wait_window(d)
        if d.result:
            try:
                self.controller.store.add_staff(d.result["sid"], d.result["pwd"], d.result["name"])
                messagebox.showinfo("OK", "Staff added.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def edit_staff(self):
        d = FormDialog(self, "Edit Staff", [
            {"label": "Staff ID", "key": "sid", "type": "text"},
            {"label": "New Name (optional)", "key": "name", "type": "text"},
            {"label": "New Password (optional)", "key": "pwd", "type": "password"},
        ], submit_text="Save")
        self.wait_window(d)
        if d.result:
            try:
                self.controller.store.edit_staff(d.result["sid"],
                                                 new_name=(d.result["name"] or None),
                                                 new_password=(d.result["pwd"] or None))
                messagebox.showinfo("OK", "Staff updated.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def remove_staff(self):
        d = FormDialog(self, "Remove Staff", [
            {"label": "Staff ID", "key": "sid", "type": "text"},
        ], submit_text="Remove")
        self.wait_window(d)
        if d.result:
            try:
                self.controller.store.remove_staff(d.result["sid"])
                messagebox.showinfo("OK", "Staff removed.")
            except Exception as e:
                messagebox.showerror("Error", str(e))


class StaffFrame(ttk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller

        top = ttk.Frame(self); top.pack(fill="x", pady=8)
        ttk.Label(top, text="Staff Panel", font=("Arial", 20, "bold")).pack(side="left", padx=8)
        ttk.Button(top, text="Logout", command=lambda: controller.show_frame("LoginFrame")).pack(side="right", padx=8)

        # search & table to view accounts
        sb = ttk.Frame(self); sb.pack(fill="x", pady=4)
        self.search_txt = tk.StringVar()
        ttk.Entry(sb, textvariable=self.search_txt, width=30).pack(side="left", padx=6)
        ttk.Button(sb, text="Search by Name", command=self.search_name).pack(side="left", padx=4)
        ttk.Button(sb, text="Search by Account", command=self.search_acc).pack(side="left", padx=4)
        ttk.Button(sb, text="Show All", command=self.refresh).pack(side="left", padx=4)

        cols = ("Name", "Age", "Email", "AccountNo", "PIN", "Balance")
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=14)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=150 if c != "Email" else 220, anchor="center")
        self.tree.pack(fill='both', expand=True, padx=8, pady=6)

        btns = ttk.Frame(self); btns.pack(pady=6)
        ttk.Button(btns, text="Deposit", command=self.deposit).pack(side='left', padx=5)
        ttk.Button(btns, text="Withdraw", command=self.withdraw).pack(side='left', padx=5)
        ttk.Button(btns, text="Update (name/age/email)", command=self.update_user).pack(side='left', padx=5)

    def on_show(self):
        self.refresh()

    def _fill_table(self, accounts):
        self.tree.delete(*self.tree.get_children())
        for acc in accounts:
            accno = acc.get("accountNo") or acc.get("accountNo.")
            self.tree.insert('', 'end', values=(acc['name'], acc['age'], acc['email'], accno, acc['pin'], acc['balance']))

    def refresh(self):
        self._fill_table(self.controller.store.data["accounts"])

    def search_name(self):
        q = self.search_txt.get().strip()
        self._fill_table(self.controller.store.search(name=q) if q else self.controller.store.data["accounts"])

    def search_acc(self):
        q = self.search_txt.get().strip()
        self._fill_table(self.controller.store.search(acc_no=q) if q else self.controller.store.data["accounts"])

    def _acc_prompt(self, title, need_pin=False, need_amount=False):
        fields = [{"label": "Account No", "key": "acc", "type": "text"}]
        if need_pin:
            fields.append({"label": "PIN", "key": "pin", "type": "int"})
        if need_amount:
            fields.append({"label": "Amount", "key": "amt", "type": "int"})
        d = FormDialog(self, title, fields, submit_text="OK")
        self.wait_window(d)
        return d.result

    def deposit(self):
        res = self._acc_prompt("Deposit", need_pin=True, need_amount=True)
        if not res: return
        try:
            bal = self.controller.store.deposit(res["acc"], res["pin"], res["amt"])
            messagebox.showinfo("Success", f"New Balance: {bal}")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def withdraw(self):
        res = self._acc_prompt("Withdraw", need_pin=True, need_amount=True)
        if not res: return
        try:
            bal = self.controller.store.withdraw(res["acc"], res["pin"], res["amt"])
            messagebox.showinfo("Success", f"New Balance: {bal}")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_user(self):
        d = FormDialog(self, "Update User", [
            {"label": "Account No", "key": "acc", "type": "text"},
            {"label": "Field (name/age/email)", "key": "field", "type": "text"},
            {"label": "New Value", "key": "value", "type": "text"},
        ], submit_text="Update")
        self.wait_window(d)
        if d.result:
            try:
                self.controller.store.update_account(d.result["acc"], **{d.result["field"]: d.result["value"]})
                messagebox.showinfo("OK", "Updated successfully")
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))


class UserFrame(ttk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller
        self.current_user = None

        top = ttk.Frame(self); top.pack(fill="x", pady=8)
        ttk.Label(top, text="User Panel", font=("Arial", 20, "bold")).pack(side="left", padx=8)
        ttk.Button(top, text="Logout", command=lambda: controller.show_frame("LoginFrame")).pack(side="right", padx=8)

        self.info = tk.Text(self, height=16)
        self.info.pack(fill='both', expand=True, padx=8, pady=8)

        ttk.Button(self, text="Reset PIN", command=self.reset_pin).pack(pady=6)

    def on_show(self):
        self.show_details()

    def show_details(self):
        self.info.delete(1.0, tk.END)
        if self.current_user:
            accno = self.current_user.get("accountNo") or self.current_user.get("accountNo.")
            # show all details (including PIN, as requested earlier)
            ordered = {
                "name": self.current_user.get("name"),
                "age": self.current_user.get("age"),
                "email": self.current_user.get("email"),
                "accountNo": accno,
                "pin": self.current_user.get("pin"),
                "balance": self.current_user.get("balance"),
            }
            for k, v in ordered.items():
                self.info.insert(tk.END, f"{k}: {v}\n")

    def reset_pin(self):
        if not self.current_user:
            return
        d = FormDialog(self, "Reset PIN", [
            {"label": "Old PIN", "key": "old", "type": "int"},
            {"label": "New PIN (4-digit)", "key": "new", "type": "int"},
        ], submit_text="Change")
        self.wait_window(d)
        if d.result:
            try:
                accno = self.current_user.get("accountNo") or self.current_user.get("accountNo.")
                self.controller.store.reset_pin(accno, d.result["old"], d.result["new"])
                messagebox.showinfo("Success", "PIN reset successfully")
                # reload current user details
                self.current_user = self.controller.store.search(acc_no=accno)[0]
                self.show_details()
            except Exception as e:
                messagebox.showerror("Error", str(e))


#############################
# Main Entry
#############################
if __name__ == "__main__":
    store = DataStore()
    app = App(store)
    app.mainloop()
