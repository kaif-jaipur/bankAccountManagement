import tkinter as tk
from tkinter import messagebox, simpledialog
import json, random, string
from pathlib import Path


class Bank:
    database = 'data.json'
    data = []

    try:
        if Path(database).exists():
            with open(database) as fs:
                data = json.loads(fs.read())
        else:
            print("no such file exist")
    except Exception as err:
        print(f"An exception occurred: {err}")

    @classmethod
    def __update(cls):
        with open(cls.database, 'w') as fs:
            fs.write(json.dumps(cls.data, indent=4))

    @classmethod
    def __account_generate(cls):
        alpha = random.choices(string.ascii_letters, k=3)
        num = random.choices(string.digits, k=3)
        spchar = random.choices("!@#%^&*", k=1)
        acc_id = alpha + num + spchar
        random.shuffle(acc_id)
        return "".join(acc_id)

    @classmethod
    def createAccount(cls, name, age, email, pin):
        info = {
            "name": name,
            "age": age,
            "email": email,
            "pin": pin,
            "accountNo.": Bank.__account_generate(),
            "balance": 0
        }
        if info['age'] < 18 or len(str(info["pin"])) != 4:
            return None
        else:
            cls.data.append(info)
            Bank.__update()
            return info

    @classmethod
    def depositMoney(cls, accnumber, pin, amount):
        userdata = [i for i in Bank.data if i['accountNo.'] == accnumber and i['pin'] == pin]
        if userdata == []:
            return False
        else:
            if amount > 10000 or amount <= 0:
                return "limit"
            userdata[0]['balance'] += amount
            Bank.__update()
            return True

    @classmethod
    def withdrawMoney(cls, accnumber, pin, amount):
        userdata = [i for i in Bank.data if i['accountNo.'] == accnumber and i['pin'] == pin]
        if userdata == []:
            return False
        else:
            if amount > userdata[0]['balance'] or amount <= 0:
                return "limit"
            userdata[0]['balance'] -= amount
            Bank.__update()
            return True

    @classmethod
    def getDetails(cls, accnumber, pin):
        userdata = [i for i in Bank.data if i['accountNo.'] == accnumber and i['pin'] == pin]
        if userdata == []:
            return None
        return userdata[0]

    @classmethod
    def deleteAccount(cls, accnumber, pin):
        userdata = [i for i in Bank.data if i['accountNo.'] == accnumber and i['pin'] == pin]
        if userdata == []:
            return False
        cls.data.remove(userdata[0])
        Bank.__update()
        return True


# GUI
root = tk.Tk()
root.title("Bank Management System")
root.geometry("500x400")


def create_account():
    name = simpledialog.askstring("Name", "Enter your name")
    age = simpledialog.askinteger("Age", "Enter your age")
    email = simpledialog.askstring("Email", "Enter your email")
    pin = simpledialog.askinteger("PIN", "Enter 4-digit pin")

    info = Bank.createAccount(name, age, email, pin)
    if info:
        messagebox.showinfo("Success", f"Account Created!\nAccount No: {info['accountNo.']}")
    else:
        messagebox.showerror("Error", "Invalid details! Age must be >=18 and PIN must be 4 digits.")


def deposit_money():
    acc = simpledialog.askstring("Account", "Enter your account number")
    pin = simpledialog.askinteger("PIN", "Enter your PIN")
    amt = simpledialog.askinteger("Amount", "Enter amount to deposit")
    result = Bank.depositMoney(acc, pin, amt)
    if result is True:
        messagebox.showinfo("Success", "Money deposited successfully")
    elif result == "limit":
        messagebox.showerror("Error", "Deposit must be between 1 and 10000")
    else:
        messagebox.showerror("Error", "Account not found")


def withdraw_money():
    acc = simpledialog.askstring("Account", "Enter your account number")
    pin = simpledialog.askinteger("PIN", "Enter your PIN")
    amt = simpledialog.askinteger("Amount", "Enter amount to withdraw")
    result = Bank.withdrawMoney(acc, pin, amt)
    if result is True:
        messagebox.showinfo("Success", "Money withdrawn successfully")
    elif result == "limit":
        messagebox.showerror("Error", "Invalid amount or insufficient balance")
    else:
        messagebox.showerror("Error", "Account not found")


def view_details():
    acc = simpledialog.askstring("Account", "Enter your account number")
    pin = simpledialog.askinteger("PIN", "Enter your PIN")
    data = Bank.getDetails(acc, pin)
    if data:
        details = "\n".join([f"{k}: {v}" for k, v in data.items()])
        messagebox.showinfo("Account Details", details)
    else:
        messagebox.showerror("Error", "Account not found")


def delete_account():
    acc = simpledialog.askstring("Account", "Enter your account number")
    pin = simpledialog.askinteger("PIN", "Enter your PIN")
    result = Bank.deleteAccount(acc, pin)
    if result:
        messagebox.showinfo("Success", "Account deleted successfully")
    else:
        messagebox.showerror("Error", "Account not found")


# Buttons
tk.Button(root, text="Create Account", width=20, command=create_account).pack(pady=5)
tk.Button(root, text="Deposit Money", width=20, command=deposit_money).pack(pady=5)
tk.Button(root, text="Withdraw Money", width=20, command=withdraw_money).pack(pady=5)
tk.Button(root, text="Check Details", width=20, command=view_details).pack(pady=5)
tk.Button(root, text="Delete Account", width=20, command=delete_account).pack(pady=5)
tk.Button(root, text="Exit", width=20, command=root.quit).pack(pady=5)

root.mainloop()
