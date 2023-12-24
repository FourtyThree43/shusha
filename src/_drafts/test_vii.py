from tkinter import ttk
import tkinter as tk

root = tk.Tk()
root.geometry("750x450")
root.title("Tkinter Pack layout Example")
root.iconbitmap("../gui/assets/beanonymous.ico")
# root.state(newstate="zoomed")

main_menu = tk.Menu(root)
root.config(menu=main_menu, padx=10, pady=10)

file_menu = tk.Menu(main_menu, tearoff=0)
main_menu.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="New")
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

upper_frame = tk.Frame(root, bg="red", height=50)
upper_frame.pack(fill="both", expand=True)

center_frame = tk.Frame(root, bg="green", height=150)
center_frame.pack(fill="both", expand=True)

# Center PanedWindow
pw = ttk.PanedWindow(center_frame, orient=tk.HORIZONTAL, width=100, height=100)
pw.pack(fill=tk.BOTH, expand=True)

left_list = tk.Listbox(pw, height=100, width=20)
pw.add(left_list)

right_list = tk.Listbox(pw, bg="pink", height=100, width=50)
pw.add(right_list)

bottom_list = ttk.Treeview(pw)
pw.add(bottom_list)

# add items to left_list
for i in range(1, 22):
    left_list.insert(tk.END, f"Item {i}")

# add items to right_list
for i in range(1, 22):
    right_list.insert(tk.END, f"Item {i}")

# add items to bottom_list
for i in range(1, 22):
    bottom_list.insert("", tk.END, text=f"Item {i}")

bottom_frame = tk.Frame(root, bg="blue", height=250)
bottom_frame.pack(fill="both", expand=True)

button = tk.Button(bottom_frame, text="Click Me")
button.pack(padx=10, pady=10, side=tk.LEFT)

button2 = tk.Button(bottom_frame, text="Click Me")
button2.pack(padx=10, pady=10, side=tk.LEFT)

button3 = tk.Button(bottom_frame, text="Click Me")
button3.pack(padx=10, pady=10, side=tk.LEFT)

root.mainloop()
