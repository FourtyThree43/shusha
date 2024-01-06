import tkinter as tk

# Create the main window
root = tk.Tk()
root.title("Application Name")

# Create the menu bar
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# Create the dropdown menus
for _ in range(5):
    menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Menu Item", menu=menu)
    for header in ["Header A", "Header B", "Header C"]:
        menu.add_command(label=header)

# Create the side bar
side_frame = tk.Frame(root, bg='#D3D3D3')
side_frame.pack(side=tk.LEFT, fill=tk.BOTH)

for _ in range(4):
    btn = tk.Button(side_frame, text="Nav Item", anchor='w', padx=20)
    btn.pack(fill=tk.X)

# Create the main content area
content_frame = tk.Frame(root, bg='#FFFFFF')
content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create the settings button
settings_button = tk.Button(root, text="Settings")
settings_button.pack(side=tk.BOTTOM, anchor='w')

# Run the application
root.mainloop()
