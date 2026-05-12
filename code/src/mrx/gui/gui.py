import tkinter as tk
from PIL import Image, ImageTk

BACKGROUND = "#1e1e1e"
BUTTON = "#3a3a3a"
BUTTON_PRESS = "#505050"
TEXT = "#ffffff"


class Gui:
    def __init__(self):
        self.root = tk.Tk()
        self.root.configure(bg=BACKGROUND)
        self.root.title("MrX")
        self.root.geometry("1600x900")
        self.root.state("zoomed")

        self.accuracy = 100
        self.username = ""
        self.password = ""

        container = tk.Frame(self.root, bg=BACKGROUND)
        container.pack(fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for scene in (LoginScene, SignupScene, HomeScene):
            frame = scene(container, self)
            self.frames[scene] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_scene(LoginScene)

    def show_scene(self, scene):
        self.frames[scene].tkraise()

    def start(self):
        self.root.mainloop()

class LoginScene(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BACKGROUND)
        self.app = app

        signup_frm = tk.Frame(self, bg=BACKGROUND)
        signup_frm.pack(fill="x")

        login_frm = tk.Frame(self, bg=BACKGROUND)
        login_frm.pack()

        tk.Button(
            signup_frm,
            text="Sign up",
            command=self.signup,
            fg=TEXT,
            bg=BUTTON,
            activebackground=BUTTON_PRESS,
            relief="flat"
        ).pack(side="right", pady=30, padx=30)

        tk.Label(
            login_frm ,
            text="Login",
            fg=TEXT,
            bg=BACKGROUND,
            font=("Arial", 24)
        ).pack(pady=(100,40))

        self.user_ent = tk.Entry(
            login_frm ,
            fg=TEXT,
            bg=BACKGROUND,
            insertbackground=TEXT
        )
        self.user_ent.pack(pady=10)

        self.pw_ent = tk.Entry(
            login_frm ,
            fg=TEXT,
            bg=BACKGROUND,
            insertbackground=TEXT,
            show="*"
        )
        self.pw_ent.pack(pady=10)

        tk.Button(
            login_frm ,
            text="Enter",
            command=self.login,
            fg=TEXT,
            bg=BUTTON,
            activebackground=BUTTON_PRESS,
            relief="flat"
        ).pack(pady=20)

    def login(self):
        self.app.username = self.user_ent.get()
        self.app.password = self.pw_ent.get()
        self.app.show_scene(HomeScene)

    def signup(self):
        self.app.username = self.user_ent.get()
        self.app.password = self.pw_ent.get()
        self.app.show_scene(SignupScene)

class SignupScene(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BACKGROUND)
        self.app = app

        login_frm = tk.Frame(self, bg=BACKGROUND)
        login_frm.pack(fill="x")

        signup_frm = tk.Frame(self, bg=BACKGROUND)
        signup_frm.pack()

        tk.Button(
            login_frm,
            text="Log in",
            command=self.login,
            fg=TEXT,
            bg=BUTTON,
            activebackground=BUTTON_PRESS,
            relief="flat"
        ).pack(side="right", pady=30, padx=30)

        tk.Label(
            signup_frm ,
            text="Signup",
            fg=TEXT,
            bg=BACKGROUND,
            font=("Arial", 24)
        ).pack(pady=(100,40))

        self.user_ent = tk.Entry(
            signup_frm ,
            fg=TEXT,
            bg=BACKGROUND,
            insertbackground=TEXT
        )
        self.user_ent.pack(pady=10)

        self.pw_ent = tk.Entry(
            signup_frm ,
            fg=TEXT,
            bg=BACKGROUND,
            insertbackground=TEXT,
            show="*"
        )
        self.pw_ent.pack(pady=10)

        tk.Button(
            signup_frm ,
            text="Enter",
            command=self.signup,
            fg=TEXT,
            bg=BUTTON,
            activebackground=BUTTON_PRESS,
            relief="flat"
        ).pack(pady=20)

    def login(self):
        self.app.username = self.user_ent.get()
        self.app.password = self.pw_ent.get()
        self.app.show_scene(LoginScene)

    def signup(self):
        self.app.username = self.user_ent.get()
        self.app.password = self.pw_ent.get()
        self.app.show_scene(HomeScene)

class HomeScene(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BACKGROUND)
        self.app = app

        image = Image.open("./src/mrx/img/map.jpg")
        self.photo = ImageTk.PhotoImage(image)

        self.acc_lbl = tk.Label(
            self,
            text=f"Current accuracy: {app.accuracy}m",
            font=("Arial", 16),
            fg=TEXT,
            bg=BACKGROUND
        )
        self.acc_lbl.pack(pady=10)

        control_frm = tk.Frame(self, bg=BACKGROUND)
        control_frm.pack(pady=10)

        self.acc_ent = tk.Entry(
            control_frm,
            fg=TEXT,
            bg=BACKGROUND,
            insertbackground=TEXT
        )
        self.acc_ent.pack(side="left", padx=10)

        acc_btn = tk.Button(
            control_frm,
            text="Set accuracy",
            command=self.update_accuracy,
            fg=TEXT,
            bg=BUTTON,
            activebackground=BUTTON_PRESS,
            relief="flat"
        )
        acc_btn.pack(side="left")

        logout_btn = tk.Button(
            control_frm,
            text="Logout",
            command=lambda: app.show_scene(LoginScene),
            fg=TEXT,
            bg=BUTTON,
            activebackground=BUTTON_PRESS,
            relief="flat"
        )
        logout_btn.pack(padx=10)

        map_frm = tk.Frame(self, bg=BACKGROUND)
        map_frm.pack()

        map_lbl = tk.Label(map_frm, image=self.photo)
        map_lbl.pack(pady=20)

    def update_accuracy(self):
        try:
            self.app.accuracy = int(self.acc_ent.get())
            self.acc_lbl.config(text=f"Current accuracy: {self.app.accuracy}m")
        except ValueError:
            pass

def main():
    Gui().start()