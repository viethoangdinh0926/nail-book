from tkcalendar import Calendar
from babel.dates import format_date, parse_date, get_day_names, get_month_names
from babel.numbers import *
import functools
import os
import errno
from os import path, listdir
try:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox, OptionMenu
except ImportError:
    import Tkinter as tk
    import ttk
    from Tkinter import messagebox, OptionMenu

cal = None

people = {}
bg_colors = ["gray", "#FFFFFF", "#75BDF1"]
start_appt_time_menu_widget = None
start_time_var = None
start_time_var_trace_id = None
min_start_idx = 0
end_appt_time_menu_widget = None
end_time_var = None
end_time_var_trace_id = None
max_end_idx = 0
picked_appt_start_time = ""
picked_appt_end_time = ""

start_time_of_day = None
end_time_of_day = None
time_slot_num = 0

class MyCalendar(Calendar):
    def get_displayed_month_year(self):
        return self._date.month, self._date.year

def on_change_month(event):
    # remove previously displayed events
    cal.calevent_remove('all')
    year, month= cal.get_displayed_month_year()
    # display the current month events 
    # ...

class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()

def update_timeboard(top_widget, timeboard_date):
    global people
    bg_color = bg_colors[1]
    fg_color = bg_colors[0]
    
    frame = top_widget.nametowidget("main_frame")
    for r in range(time_slot_num):
        tk.Grid.rowconfigure(frame, r + 2, weight=1)
        h = (r // 4) + start_time_of_day
        m = (r % 4) * 15
        if r % 4 == 0:
        #    if bg_color == bg_colors[0]:
        #        bg_color = bg_colors[1]
        #    else:
        #        bg_color = bg_colors[0]
            tk.Label(frame, text=h, borderwidth=2, relief="groove", bg=bg_color, font=("Courier", 20)).grid(row=r+2, column=0, rowspan=4, sticky="nsew")

        tk.Label(frame, text="%02d"%(m), borderwidth=2, relief="groove", bg=bg_color, fg="#CA4F5F", font=("Courier", 10)).grid(row=r+2, column=1, sticky="nsew")  
        for c in range(len(people)):  
            tk.Grid.columnconfigure(frame, c + 2, weight=1)
            lb_name = "p" + str(c+1) + "-" + str(h) + "-" + str(m)
            lb = tk.Label(frame, text="%02d"%(h) + ":" + "%02d"%(m), borderwidth=2, relief="groove", bg=bg_color, fg=fg_color, name=lb_name)
            lb.grid(row=r+2, column=c+2, sticky="nsew")
            lb.bind("<Button-1>", functools.partial(mouse_click_on_time_cell_handler, top_widget=top_widget, lb_time=str(h)+"-"+str(m), person="p"+str(c+1), date=timeboard_date))

    appt_path = "data\\" + str(timeboard_date)

    if not path.exists(appt_path):
        return

    appt_folders = [d for d in listdir(appt_path) if not path.isfile(path.join(appt_path, d))]
    for folder in appt_folders:
        folder_path = appt_path + "\\" + folder
        appt_files = [f for f in listdir(folder_path) if path.isfile(path.join(folder_path, f))]
        appt_arr = [0]*time_slot_num
        for name in appt_files:
            color = bg_colors[1]
            for i in range(len(appt_arr)):
                m = (i % 4) * 15 
                h = (i // 4) + start_time_of_day
                widget_path_name = "main_frame." + folder + "-" + str(h) + "-" + str(m)
                #if (i % 4) == 0:
                #    if color == bg_colors[0]:
                #        color = bg_colors[1]
                #    else:
                #        color = bg_colors[0]
                top_widget.nametowidget(widget_path_name).configure(bg = color)

            appt_time = name.split("---")
            try:
                fd = open(folder_path + "\\" + name, 'r')
                content = fd.read()
                str_start_time = appt_time[0]
                str_end_time = appt_time[1]
                start_time = str_start_time.split("-")
                end_time = str_end_time.split("-")
                start_index = (int(start_time[0]) - start_time_of_day) * 4 + int(start_time[1]) // 15
                end_index = (int(end_time[0]) - start_time_of_day) * 4 + int(end_time[1]) // 15
                for i in range(start_index, end_index):
                    m = (i % 4) * 15 
                    h = (i // 4) + start_time_of_day
                    widget_path_name = "main_frame." + folder + "-" + str(h) + "-" + str(m)
                    if i == start_index:
                        end_m = (end_index % 4) * 15
                        end_h = (end_index // 4) + start_time_of_day
                        CreateToolTip(top_widget.nametowidget(widget_path_name), "From " + "%02d"%(h) + ":" + "%02d"%(m) + " to " + "%02d"%(end_h) + ":" + "%02d"%(end_m)  )
                        top_widget.nametowidget(widget_path_name)['fg'] = '#0013FF'
                        top_widget.nametowidget(widget_path_name).grid(rowspan = end_index - start_index)
                        top_widget.nametowidget(widget_path_name)['text'] = content
                    else:
                        top_widget.nametowidget(widget_path_name).grid_forget()
                    appt_arr[i] = 1
            except:
                messagebox.showerror("ERROR", "Invalid file found in: " + appt_path, parent=top_widget)
                return
        for i in range(len(appt_arr)):
            if appt_arr[i] != 0:
                m = (i % 4) * 15 
                h = (i // 4) + start_time_of_day
                try:
                    widget_path_name = "main_frame." + folder + "-" + str(h) + "-" + str(m)
                    top_widget.nametowidget(widget_path_name).configure(bg=bg_colors[2])
                except:
                    tk.messagebox.showerror("ERROR", "Invalid personal directory found in: " + appt_path, parent=top_widget)
                    return

def create_appointment_handler(top_widget, appt_window, timeboard_date, person, comment_widget):
    global picked_appt_start_time, picked_appt_end_time

    if comment_widget.get("1.0", "end-1c") == "":
        tk.messagebox.showinfo("NOTICE", "Please enter appointment detail.", parent=appt_window)
        return

    start_time_parts = picked_appt_start_time.split(":")
    end_time_parts = picked_appt_end_time.split(":")
    time_str = "{:02d}".format(int(start_time_parts[0])) + "-" + "{:02d}".format(int(start_time_parts[1])) + "---" + "{:02d}".format(int(end_time_parts[0])) + "-" + "{:02d}".format(int(end_time_parts[1]))
    file_path = "data\\" + str(timeboard_date) + "\\" + person + "\\" + time_str

    if not path.exists(path.dirname(file_path)):
        try:
            os.makedirs(path.dirname(file_path))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                tk.messagebox.showerror("ERROR", "Failed to create appointment file at: " + file_path, parent=top_widget)
                return

    with open(file_path, "w") as f:
        f.write(comment_widget.get("1.0", "end-1c"))

    update_timeboard(top_widget, timeboard_date)

    on_window_close(top_widget, appt_window)
    appt_window.destroy()

def update_picked_appt_start_time(*args):
    global picked_appt_start_time, picked_appt_end_time, start_appt_time_menu_widget, end_appt_time_menu_widget, start_time_var, end_time_var, min_start_idx, max_end_idx, start_time_var_trace_id, end_time_var_trace_id
    picked_appt_start_time = start_time_var.get()
    start_times = picked_appt_start_time.split(":")
    start_time_idx = (int(start_times[0]) - start_time_of_day) * 4 + int(start_times[1]) // 15

    start_appt_time_menu_widget['menu'].delete(0, 'end')
    for i in range(min_start_idx, start_time_idx + 1):
        m = (i % 4) * 15 
        h = (i // 4) + start_time_of_day
        time_str = "{:02d}".format(h) + ":" + "{:02d}".format(m)
        if i == start_time_idx:
            start_time_var.set(time_str)
        start_appt_time_menu_widget['menu'].add_command(label=time_str, command=tk._setit(start_time_var, time_str))

    end_appt_time_menu_widget['menu'].delete(0, 'end')
    for i in range(start_time_idx + 1 , max_end_idx + 1):
        m = (i % 4) * 15 
        h = (i // 4) + start_time_of_day
        time_str = "{:02d}".format(h) + ":" + "{:02d}".format(m)
        #if i == start_time_idx + 1:
        #    picked_appt_end_time = time_str
        #    end_time_var.set(time_str)
        end_appt_time_menu_widget['menu'].add_command(label=time_str, command=tk._setit(end_time_var, time_str))
    

def update_picked_appt_end_time(*args):
    global picked_appt_start_time, picked_appt_end_time, start_appt_time_menu_widget, end_appt_time_menu_widget, start_time_var, end_time_var, min_start_idx, max_end_idx, start_time_var_trace_id, end_time_var_trace_id
    picked_appt_start_time = start_time_var.get()
    picked_appt_end_time = end_time_var.get()
    end_times = picked_appt_end_time.split(":")
    end_time_idx = (int(end_times[0]) - start_time_of_day) * 4 + int(end_times[1]) // 15

    start_appt_time_menu_widget['menu'].delete(0, 'end')
    for i in range(min_start_idx, end_time_idx):
        m = (i % 4) * 15 
        h = (i // 4) + start_time_of_day
        time_str = "{:02d}".format(h) + ":" + "{:02d}".format(m)
        #if i == end_time_idx - 1:
        #    picked_appt_start_time = time_str
        #    start_time_var.set(time_str)
        start_appt_time_menu_widget['menu'].add_command(label=time_str, command=tk._setit(start_time_var, time_str))
    

    end_appt_time_menu_widget['menu'].delete(0, 'end')
    for i in range(end_time_idx, max_end_idx + 1):
        m = (i % 4) * 15 
        h = (i // 4) + start_time_of_day
        time_str = "{:02d}".format(h) + ":" + "{:02d}".format(m)
        if i == end_time_idx:
            end_time_var.set(time_str)
        end_appt_time_menu_widget['menu'].add_command(label=time_str, command=tk._setit(end_time_var, time_str))


def create_appointment(top_widget, date, person, time_cell_index, appt_arr):
    global picked_appt_start_time, picked_appt_end_time, start_appt_time_menu_widget, end_appt_time_menu_widget, end_time_var, start_time_var, min_start_idx, max_end_idx, start_time_var_trace_id, end_time_var_trace_id

    min_start_idx = time_cell_index
    while min_start_idx > 0 and appt_arr[min_start_idx - 1] == 0:
        min_start_idx -= 1
    max_end_idx = time_cell_index + 1
    while max_end_idx < len(appt_arr) and appt_arr[max_end_idx] == 0:
        max_end_idx += 1
    

    top = tk.Toplevel(top_widget)
    top.title("NailBook")
    top_widget.attributes("-disabled", 1)
    top.protocol("WM_DELETE_WINDOW", functools.partial(on_window_close, parent_widget = top_widget, myself = top))
    tk.Grid.rowconfigure(top, 0, weight=1)
    tk.Grid.columnconfigure(top, 0, weight=1)
    #Create & Configure frame 
    frame = tk.Frame(top, name="main_frame")
    frame.grid(row=0, column=0, sticky="nsew")
    
    start_time_options = []
    end_time_options = []
    for i in range(min_start_idx, max_end_idx + 1):
        m = (i % 4) * 15 
        h = (i // 4) + start_time_of_day
        time_str = "{:02d}".format(h) + ":" + "{:02d}".format(m)
        if i <= time_cell_index:
            start_time_options.append(time_str)
        else:
            end_time_options.append(time_str)
    start_time_var = tk.StringVar(frame)
    start_time_var.set(start_time_options[-1]) # default value
    start_appt_time_menu_widget = OptionMenu(frame, start_time_var, *start_time_options)
    start_time_var_trace_id = start_time_var.trace("w", update_picked_appt_start_time)
    picked_appt_start_time = start_time_var.get()
    end_time_var = tk.StringVar(frame)
    end_time_var.set(end_time_options[0]) # default value
    end_appt_time_menu_widget = OptionMenu(frame, end_time_var, *end_time_options)
    end_time_var_trace_id = end_time_var.trace("w", update_picked_appt_end_time)
    picked_appt_end_time = end_time_var.get()

    tk.Label(frame, text='Start:', borderwidth=2, relief="groove").grid(row=0, column=0, sticky="nsew")
    start_appt_time_menu_widget.grid(row=0, column=1, sticky="nsew")
    tk.Label(frame, text='End:', borderwidth=2, relief="groove").grid(row=1, column=0, sticky="nsew")
    end_appt_time_menu_widget.grid(row=1, column=1, sticky="nsew")
    tk.Label(frame, text='Comment:', borderwidth=2, relief="groove").grid(row=2, column=0, sticky="nsew")
    appt_comment = tk.Text(frame, borderwidth=2, relief="groove", height=20, width=40)
    appt_comment.grid(row=2, column=1, sticky="nsew")
    create_btt = tk.Button(frame, text="OK", bg="#3E8EE3", command=functools.partial(create_appointment_handler, top_widget=top_widget, appt_window=top, timeboard_date=date, person=person, comment_widget=appt_comment))
    create_btt.grid(row=3, column=0, columnspan=2, sticky="nsew")


def update_appointment_handler(old_appt_file, old_start_idx, old_end_idx, top_widget, appt_window, timeboard_date, person, comment_widget):
    MsgBox = tk.messagebox.askquestion ('CONFIRM','Are you sure you want to update the appointment', icon='warning', parent=appt_window)
    if MsgBox == 'yes':
        try:
            os.remove(old_appt_file)
            create_appointment_handler(top_widget, appt_window, timeboard_date, person, comment_widget)
        except:
            messagebox.showerror("ERROR", "Failed to update the appointment file: " + old_appt_file, parent=top_widget)

def delete_appointment_handler(old_appt_file, old_start_idx, old_end_idx, top_widget, appt_window, timeboard_date, person):
    MsgBox = tk.messagebox.askquestion ('CONFIRM','Are you sure you want to delete the appointment', icon='warning', parent=appt_window)
    if MsgBox == 'yes':
        try:
            os.remove(old_appt_file)
            update_timeboard(top_widget, timeboard_date)
            on_window_close(top_widget, appt_window)
            appt_window.destroy()
        except:
            messagebox.showerror("ERROR", "Failed to remove the appointment file: " + old_appt_file, parent=top_widget)

def edit_delete_appointment(top_widget, timeboard_date, appointment_file, appt_arr):
    global picked_appt_start_time, picked_appt_end_time, start_appt_time_menu_widget, end_appt_time_menu_widget, end_time_var, start_time_var, min_start_idx, max_end_idx, start_time_var_trace_id, end_time_var_trace_id

    fd = open(appointment_file, 'r')
    comment = fd.read()
    fd.close()

    name_parts = appointment_file.split("\\")
    old_start_end_times = name_parts[3].split("---")
    old_start_times = old_start_end_times[0].split("-") 
    old_start_idx = (int(old_start_times[0]) - start_time_of_day) * 4 + int(old_start_times[1]) // 15
    old_end_times = old_start_end_times[1].split("-") 
    old_end_idx = (int(old_end_times[0]) - start_time_of_day) * 4 + int(old_end_times[1]) // 15

    min_start_idx = old_start_idx
    while min_start_idx > 0 and appt_arr[min_start_idx - 1] == 0:
        min_start_idx -= 1
    max_end_idx = old_end_idx
    while max_end_idx < len(appt_arr) and appt_arr[max_end_idx] == 0:
        max_end_idx += 1
    

    top = tk.Toplevel(top_widget)
    top.title("NailBook")
    top_widget.attributes("-disabled", 1)
    top.protocol("WM_DELETE_WINDOW", functools.partial(on_window_close, parent_widget = top_widget, myself = top))
    tk.Grid.rowconfigure(top, 0, weight=1)
    tk.Grid.columnconfigure(top, 0, weight=1)
    #Create & Configure frame 
    frame = tk.Frame(top, name="main_frame")
    frame.grid(row=0, column=0, sticky="nsew")
    
    start_time_options = []
    end_time_options = []
    for i in range(min_start_idx, max_end_idx + 1):
        m = (i % 4) * 15 
        h = (i // 4) + start_time_of_day
        time_str = "{:02d}".format(h) + ":" + "{:02d}".format(m)
        if i < old_end_idx:
            start_time_options.append(time_str)
        else:
            end_time_options.append(time_str)
            
    start_time_var = tk.StringVar(frame)
    start_time_var.set(start_time_options[-1]) # default value
    start_appt_time_menu_widget = OptionMenu(frame, start_time_var, *start_time_options)
    start_time_var_trace_id = start_time_var.trace("w", update_picked_appt_start_time)
    picked_appt_start_time = start_time_var.get()

    end_time_var = tk.StringVar(frame)
    end_time_var.set(end_time_options[0]) # default value
    end_appt_time_menu_widget = OptionMenu(frame, end_time_var, *end_time_options)
    end_time_var_trace_id = end_time_var.trace("w", update_picked_appt_end_time)
    picked_appt_end_time = end_time_var.get()

    tk.Label(frame, text='Start:', borderwidth=2, relief="groove").grid(row=0, column=0, sticky="nsew")
    start_appt_time_menu_widget.grid(row=0, column=1, sticky="nsew")
    tk.Label(frame, text='End:', borderwidth=2, relief="groove").grid(row=1, column=0, sticky="nsew")
    end_appt_time_menu_widget.grid(row=1, column=1, sticky="nsew")
    tk.Label(frame, text='Comment:', borderwidth=2, relief="groove").grid(row=2, column=0, sticky="nsew")
    appt_comment = tk.Text(frame, borderwidth=2, relief="groove", height=20, width=40)
    appt_comment.grid(row=2, column=1, sticky="nsew")
    appt_comment.insert(1.0, comment)
    btt_frame = tk.Frame(frame, bg="red")
    btt_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")
    update_btt = tk.Button(btt_frame, text="Update", bg="#EFB910", command=functools.partial(update_appointment_handler, old_appt_file=appointment_file, old_start_idx=old_start_idx, old_end_idx=old_end_idx, top_widget=top_widget, appt_window=top, timeboard_date=timeboard_date, person=name_parts[2], comment_widget=appt_comment))
    update_btt.pack(side=tk.LEFT, fill=tk.BOTH,  expand=True)
    delete_btt = tk.Button(btt_frame, text="Delete", bg="#ED4F00", command=functools.partial(delete_appointment_handler, old_appt_file=appointment_file, old_start_idx=old_start_idx, old_end_idx=old_end_idx, top_widget=top_widget, appt_window=top, timeboard_date=timeboard_date, person=name_parts[2]))
    delete_btt.pack(side=tk.RIGHT, fill=tk.BOTH,  expand=True) 

def mouse_click_on_time_cell_handler(event, top_widget, lb_time, person, date):
    popup = tk.Menu(top_widget, tearoff=0)
    appt_path = "data\\" + str(date) + "\\" + person
    lb_time_elem = lb_time.split("-")
    time_cell_index = (int(lb_time_elem[0]) - start_time_of_day) * 4 + int(lb_time_elem[1]) // 15
    if path.exists(appt_path):
        appt_files = [f for f in listdir(appt_path) if path.isfile(path.join(appt_path, f))]
        appt_arr = [0]*time_slot_num
        appt_file_path = ""
        for name in appt_files:
            appt_time = name.split("---")
            try:
                str_start_time = appt_time[0]
                str_end_time = appt_time[1]
                start_time = str_start_time.split("-")
                end_time = str_end_time.split("-")
                start_index = (int(start_time[0]) - start_time_of_day) * 4 + int(start_time[1]) // 15
                end_index = (int(end_time[0]) - start_time_of_day) * 4 + int(end_time[1]) // 15
                for i in range(start_index, end_index):
                    appt_arr[i] = 1
                    if i == time_cell_index:
                        appt_file_path = appt_path + "\\" + name
            except:
                tk.messagebox.showerror("ERROR", "Invalid file found in: " + appt_path, parent=top_widget)
                return
        
        if(appt_arr[time_cell_index] == 1):
            popup.add_command(label="Edit or delete appointment", command=functools.partial(edit_delete_appointment, top_widget=top_widget, timeboard_date=date, appointment_file=appt_file_path, appt_arr=appt_arr)) # , command=next) etc...
        else:
            popup.add_command(label="Create appointment", command=functools.partial(create_appointment, top_widget=top_widget, date=date, person=person, time_cell_index=time_cell_index, appt_arr=appt_arr ))
    else:
        #popup.add_separator()
        popup.add_command(label="Create appointment", command=functools.partial(create_appointment, top_widget=top_widget, date=date, person=person, time_cell_index=time_cell_index, appt_arr=[0]*time_slot_num))
    # display the popup menu
    try:
        popup.tk_popup(event.x_root, event.y_root, 0)
    finally:
        # make sure to release the grab (Tk 8.0a1 only)
        popup.grab_release()

def on_window_close(parent_widget, myself):
    try:
        parent_widget['state'] = tk.NORMAL
    except:
        parent_widget.attributes("-disabled", 0)

    myself.destroy()

def on_select_date(event):
    global people
    date = cal.selection_get()

    # disable the calendar when processing current date
    cal['state'] = tk.DISABLED

    top = tk.Toplevel(root)
    top.protocol("WM_DELETE_WINDOW", functools.partial(on_window_close, parent_widget = cal, myself = top))
    top.state('zoomed')
    tk.Grid.rowconfigure(top, 0, weight=1)
    tk.Grid.columnconfigure(top, 0, weight=1)
    #Create & Configure frame 
    frame = tk.Frame(top, name="main_frame")
    frame.grid(row=0, column=0, sticky="nsew")
    tk.Label(frame, text='%s'%(date), borderwidth=2, relief="groove", fg='#DF3F3F', font=("Courier", 30)).grid(row=0, column=0, columnspan=len(people)+2, sticky="nsew")
    tk.Label(frame, text='', borderwidth=2, relief="groove").grid(row=1, column=0, columnspan=2, sticky="nsew")
    for c in range(len(people)):
        tk.Label(frame, text=people["p"+str(c+1)], borderwidth=2, relief="groove", bg='yellow', fg='#2F8694', font=("Courier", 20) ).grid(row=1, column=c+2, sticky="nsew")

    update_timeboard(top, date)

def create_calendar():
    global cal

    cal = MyCalendar(root)
    root.state('zoomed')
    cal.pack(expand = True, fill = tk.BOTH)

    cal.bind('<<CalendarMonthChanged>>', on_change_month)
    cal.bind('<<CalendarSelected>>', on_select_date)

def create_app_config_handler(config_window, open_hour_var, close_hour_var, employee_list_widget):
    global time_slot_num, start_time_of_day, end_time_of_day

    employee_str = employee_list_widget.get("1.0", "end-1c")
    if employee_str == "":
        tk.messagebox.showinfo("NOTICE", "Please enter employee names, separated by commas.", parent=config_window)
        return
    
    employee_names = employee_str.split(",")
    for i in range(len(employee_names)):
        people["p" + str(i + 1)] = employee_names[i].strip()

    start_hour_str = open_hour_var.get()
    start_time_of_day = int(start_hour_str.split(":")[0])
    close_hour_str = close_hour_var.get()
    end_time_of_day = int(close_hour_str.split(":")[0])
    time_slot_num = (end_time_of_day - start_time_of_day + 1) * 4

    file_path = "config\\nailbook.conf"
    if not path.exists(path.dirname(file_path)):
        try:
            os.makedirs(path.dirname(file_path))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                messagebox.showerror("ERROR", "Failed to create appointment file at: " + file_path, parent=config_window)
                return
    with open(file_path, "w") as f:
        f.write("start-time-of-day=" + start_hour_str + "\n")
        f.write("end-time-of-day=" + close_hour_str)

    file_path = "config\\employee"
    with open(file_path, "w") as f:
        for name in employee_names:
            f.write(name.strip() + "\n")

    config_window.nametowidget("main_frame").destroy()
    create_calendar()

root = tk.Tk()
root.title("NailBook")

# Check if saved setting exists and is valid
config_path = "config\\nailbook.conf"
name_file_path = "config\\employee"
if path.exists(config_path) and path.exists(name_file_path):
    with open(config_path) as fd:
        line = fd.readline()
        while line:
            params = line.split("=")
            if params[0] == "start-time-of-day":
                start_time_of_day = int(params[1].split(":")[0])
            elif params[0] == "end-time-of-day":
                end_time_of_day = int(params[1].split(":")[0])
            line = fd.readline()
        time_slot_num = (end_time_of_day - start_time_of_day + 1) * 4
    if (start_time_of_day is None) or (end_time_of_day is None):
        messagebox.showerror("ERROR", config_path + ": Invalid config file! please remove it and try again.")
        exit()
    
    with open(name_file_path) as fd:
        count = 1
        line = fd.readline()
        while line:
            name = line.strip()
            people["p" + str(count)] = name
            count += 1
            line = fd.readline()
    if len(people.keys()) == 0:
        messagebox.showerror("ERROR", name_file_path + ": Invalid employee name file! please remove it and try again.")
        exit()

    create_calendar()
else:
    setup_w = root
    tk.Grid.rowconfigure(setup_w, 0, weight=1)
    tk.Grid.columnconfigure(setup_w, 0, weight=1)
    #Create & Configure frame 
    frame = tk.Frame(setup_w, name="main_frame")
    frame.grid(row=0, column=0, sticky="nsew")
    tk.Label(frame, text="SETTING", borderwidth=2, relief="groove", fg='#DF3F3F', font=("Courier", 30)).grid(row=0, column=0, columnspan=2, sticky="nsew")

    var1 = tk.StringVar(frame)
    open_time_options = ["7:00", "8:00", "9:00", "10:00", "11:00"]
    var1.set(open_time_options[0]) # default value
    open_time_menu = OptionMenu(frame, var1, *open_time_options)

    var2 = tk.StringVar(frame)
    close_time_options = ["14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00"]
    var2.set(close_time_options[0]) # default value
    close_time_menu = OptionMenu(frame, var2, *close_time_options)


    tk.Label(frame, text='Open hour:', borderwidth=2, relief="groove").grid(row=1, column=0, sticky="nsew")
    open_time_menu.grid(row=1, column=1, sticky="nsew")
    tk.Label(frame, text='Close hour:', borderwidth=2, relief="groove").grid(row=2, column=0, sticky="nsew")
    close_time_menu.grid(row=2, column=1, sticky="nsew")
    tk.Label(frame, text='Employee Names (comma seperated)', borderwidth=2, relief="groove").grid(row=3, column=0, sticky="nsew")
    employee_list = tk.Text(frame, borderwidth=2, relief="groove", height=20, width=40)
    employee_list.grid(row=3, column=1, sticky="nsew")
    create_btt = tk.Button(frame, text="OK", bg="#3E8EE3", command=functools.partial(create_app_config_handler, config_window=setup_w, open_hour_var=var1, close_hour_var=var2, employee_list_widget=employee_list))
    create_btt.grid(row=4, column=0, columnspan=2, sticky="nsew")

root.mainloop()