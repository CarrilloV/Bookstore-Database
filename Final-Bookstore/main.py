import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import Button
from tkinter import Toplevel
from tkinter import Radiobutton
import sqlite3

# create a dictionary to store the usernames and passwords
users = {
    "admin": "admin",
    "user1": "password1",
    "nichole": "bread",
    "victor": "is cool"
}

# create a connection to the bookstore database
conn_bookstore = sqlite3.connect("bookstore.db")
cursor_bookstore = conn_bookstore.cursor()

# create the books table if it does not exist
cursor_bookstore.execute('''CREATE TABLE IF NOT EXISTS books
                (id INTEGER PRIMARY KEY,
                 title TEXT,
                 author TEXT,
                 publisher TEXT,
                 price REAL,
                 availability INTEGER)''')

# close the connection to the database
conn_bookstore.commit()
conn_bookstore.close()

# create a connection to the users database
conn_users = sqlite3.connect("users.db")
cursor_users = conn_users.cursor()

# create the users table if it does not exist
cursor_users.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY,
                 username TEXT,
                 password TEXT)''')

# close the connection to the database
conn_users.commit()
conn_users.close()

# connect to orders database
conn_orders = sqlite3.connect("orders.db")
cursor_orders = conn_orders.cursor()

# create the orders table if it does not exist
cursor_orders.execute('''CREATE TABLE IF NOT EXISTS orders
                (id INTEGER PRIMARY KEY,
                 num_books INTEGER,
                 total_price REAL)''')

# commit the changes
conn_orders.commit()


def login():
    username = username_entry.get()
    password = password_entry.get()

    # connect to the users database
    conn_users = sqlite3.connect("users.db")
    cursor_users = conn_users.cursor()

    # check if the username and password are valid
    query = "SELECT * FROM users WHERE username=? AND password=?"
    cursor_users.execute(query, (username, password))
    user = cursor_users.fetchone()
    if user:
        # if the user is the admin, open the admin panel
        if username == "admin" and password == "secret":
            open_admin_panel()
        else:
            # otherwise, open the bookstore
            open_bookstore(conn_orders, cursor_orders)
    else:
        # otherwise, display an error message
        messagebox.showerror("Error", "Invalid username or password")

    # close the connection to the users database
    cursor_users.close()
    conn_users.close()


def register():
    # get the username and password from the entry widgets
    username = username_entry.get()
    password = password_entry.get()

    # check if the username already exists in the users table
    conn_users = sqlite3.connect("users.db")
    cursor_users = conn_users.cursor()
    cursor_users.execute("SELECT * FROM users WHERE username=?", (username,))
    existing_user = cursor_users.fetchone()

    if existing_user:
        # if the username already exists, display an error message
        messagebox.showerror("Error", "Username already exists")
    else:
        # otherwise, add the new user to the users table
        cursor_users.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn_users.commit()

        # display a success message
        messagebox.showinfo("Success", "Registration successful")

        # clear the entry widgets
        username_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)

    cursor_users.close()
    conn_users.close()


def open_bookstore(conn_orders, cursor_orders):
    global book_treeview
    cart_items = []
    # destroy the login window
    window.destroy()
    bookstore_db = "bookstore.db"
    conn = sqlite3.connect(bookstore_db)

    # create the bookstore window
    bookstore_window = tk.Tk()
    bookstore_window.title("Bookstore")
    bookstore_window.geometry("1300x450")

    # create a label for the filter
    filter_label = tk.Label(bookstore_window, text="Filter by:")
    filter_label.pack()

    # create a radio button to filter by title
    filter_var = tk.StringVar()
    filter_title_radio = tk.Radiobutton(bookstore_window, text="Title", variable=filter_var, value="Title")
    filter_title_radio.pack()

    # create a radio button to filter by author
    filter_author_radio = tk.Radiobutton(bookstore_window, text="Author", variable=filter_var, value="Author")
    filter_author_radio.pack()

    # create an entry for the filter
    filter_entry = tk.Entry(bookstore_window)
    filter_entry.pack()

    # create a button to apply the filter
    filter_button = tk.Button(bookstore_window, text="Filter", command=lambda: filter_books(book_treeview, filter_entry.get(), filter_var.get()))
    filter_button.pack()

    # create a label for the book catalog
    catalog_label = tk.Label(bookstore_window, text="Book Catalog")
    catalog_label.pack()

    book_treeview = ttk.Treeview(bookstore_window, columns=("Title", "Author", "Publisher", "Price", "Availability"))
    book_treeview.pack()

    # define the columns and headings for the Treeview
    book_treeview.heading("Title", text="Title")
    book_treeview.heading("Author", text="Author")
    book_treeview.heading("Publisher", text="Publisher")
    book_treeview.heading("Price", text="Price")
    book_treeview.heading("Availability", text="Availability")

    # retrieve the books from the database
    cursor = conn.cursor()
    query = "SELECT title, author, publisher, price, availability FROM books"
    cursor.execute(query)
    books = cursor.fetchall()

    # add the books to the Treeview
    for book in books:
        book_treeview.insert("", tk.END, values=(book[0], book[1], book[2], book[3], book[4]))

    # create a button to add a book to the shopping cart
    add_to_cart_button = Button(bookstore_window, text="Add to Cart",
                                command=lambda: add_to_cart(book_treeview, cart_items, conn))
    add_to_cart_button.pack()

    # create a button to open the shopping cart
    view_cart_button = Button(bookstore_window, text="View Cart", command=lambda: view_cart(cart_items, conn, conn_orders, cursor_orders))
    view_cart_button.pack()

    # close the connection to the database
    cursor.close()

    bookstore_window.mainloop()


def add_to_cart(book_treeview, cart_items, conn):
    selected_book = book_treeview.focus()
    if selected_book:
        book_title = book_treeview.item(selected_book)['values'][0]
        book_author = book_treeview.item(selected_book)['values'][1]
        book_publisher = book_treeview.item(selected_book)['values'][2]
        book_price = book_treeview.item(selected_book)['values'][3]
        book_availability = book_treeview.item(selected_book)['values'][4]
        if book_availability > 0:
            # update the availability in the database
            cursor = conn.cursor()
            query = "UPDATE books SET availability = ? WHERE title = ?"
            cursor.execute(query, (int(book_availability) - 1, book_title))
            conn.commit()

            cart_items.append((book_title, book_author, book_publisher, book_price))
            book_treeview.set(selected_book, column="Availability", value=int(book_availability) - 1)
        else:
            messagebox.showwarning("Out of Stock", "This book is out of stock.")
    else:
        messagebox.showwarning("No Book Selected", "Please select a book to add to cart.")


def view_cart(cart_items, conn, conn_orders, cursor_orders):
    try:
        # create the cart window
        cart_window = Toplevel()
        cart_window.title("Cart")

        # create the cart Treeview
        cart_treeview = ttk.Treeview(cart_window, columns=("Title", "Author", "Publisher", "Price"))
        cart_treeview.pack()

        # define the columns and headings for the Treeview
        cart_treeview.heading("Title", text="Title")
        cart_treeview.heading("Author", text="Author")
        cart_treeview.heading("Publisher", text="Publisher")
        cart_treeview.heading("Price", text="Price")

        # check whether the orders table exists
        try:
            cursor_orders.execute("SELECT * FROM orders LIMIT 1")
            cursor_orders.fetchone()
        except sqlite3.OperationalError:
            # if the table does not exist, create it
            cursor_orders.execute('''CREATE TABLE IF NOT EXISTS orders
                                    (id INTEGER PRIMARY KEY,
                                     num_books INTEGER,
                                     total_price REAL)''')
            conn_orders.commit()

        # get the num_books and total_price from the orders table
        cursor_orders.execute("SELECT num_books, total_price FROM orders")
        result = cursor_orders.fetchone()
        if result is None:
            num_books = 0
            total_price = 0
        else:
            num_books = result[0]
            total_price = result[1]

        payment_method = tk.StringVar()
        credit_card_radio = tk.Radiobutton(cart_window, text="Credit Card", variable=payment_method,
                                           value="Credit Card")
        credit_card_radio.pack()

        other_radio = tk.Radiobutton(cart_window, text="Other Payment Method", variable=payment_method, value="Other")
        other_radio.pack()

        # iterate through the cart items and add them to the Treeview
        for item in cart_items:
            book_title = item[0]
            book_author = item[1]
            book_publisher = item[2]
            book_price = float(item[3])
            cart_treeview.insert("", tk.END, values=[book_title, book_author, book_publisher, book_price])

        # create the Buy button and pack it into the cart window
        buy_button = Button(cart_window, text="Buy", command=lambda: buy(cart_items, conn, conn_orders, cursor_orders))
        buy_button.pack()

        # create the Remove button and pack it into the cart window
        remove_button = Button(cart_window, text="Remove", command=lambda: remove_item(cart_treeview, cart_items, cart_treeview.selection()[0]))
        remove_button.pack()

    except sqlite3.ProgrammingError as e:
        messagebox.showerror("Error", f"Cannot operate on a closed database: {e}")



def remove_item(cart_treeview, cart_items, selected_item):
    # get the index of the selected item
    index = int(selected_item[1:]) - 1

    # remove the item from the cart_items list
    cart_items.pop(index)

    # remove the item from the Treeview
    cart_treeview.delete(selected_item)


def buy(cart_items, conn, conn_orders, cursor_orders):
    try:
        # get the total number of books in the cart and the total price
        num_books = len(cart_items)
        total_price = sum(float(item[3]) for item in cart_items)

        # insert the order into the orders table
        cursor_orders.execute("INSERT INTO orders (num_books, total_price) VALUES (?, ?)", (num_books, total_price))
        conn_orders.commit()

        # clear the cart_items list
        cart_items.clear()

        messagebox.showinfo("Success", f"Order placed successfully! Total Price: ${total_price:.2f}")
    except sqlite3.ProgrammingError as e:
        messagebox.showerror("Error", f"Cannot operate on a closed database: {e}")


def filter_books(book_treeview, filter_text, filter_criteria):
    # clear the treeview
    book_treeview.delete(*book_treeview.get_children())

    # retrieve the books from the database based on the selected filter criteria
    conn = sqlite3.connect("bookstore.db")
    cursor = conn.cursor()
    if filter_criteria == "Title":
        query = "SELECT title, author, publisher, price, availability FROM books WHERE title LIKE ? ORDER BY title ASC"
    else:
        query = "SELECT title, author, publisher, price, availability FROM books WHERE author LIKE ? ORDER BY author ASC"
    cursor.execute(query, ('%' + filter_text + '%',))
    books = cursor.fetchall()
    cursor.close()
    conn.close()

    # iterate over the books and add them to the treeview
    for book in books:
        book_treeview.insert("", "end",
                             values=(book[0], book[1], book[2], book[3], book[4]))


def open_admin_panel():
    # destroy the login window
    window.destroy()

    # create the admin panel window
    admin_window = tk.Tk()
    admin_window.title("Admin Panel")
    admin_window.geometry("600x600")

    # create a label for the book catalog
    catalog_label = tk.Label(admin_window, text="Book Catalog")
    catalog_label.pack()

    # create a listbox to display the books
    book_listbox = tk.Listbox(admin_window)
    book_listbox.pack()

    # retrieve the books from the database
    conn = sqlite3.connect("bookstore.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    # add the books to the listbox
    for book in books:
        book_listbox.insert(tk.END, book[1])

    # create a frame for the add book form
    add_frame = tk.Frame(admin_window)
    add_frame.pack()

    # create a label for the add book form
    add_label = tk.Label(add_frame, text="Add Book")
    add_label.pack()

    # create entries for the add book form
    title_label = tk.Label(add_frame, text="Title")
    title_label.pack()
    global title_entry
    title_entry = tk.Entry(add_frame)
    title_entry.pack()

    author_label = tk.Label(add_frame, text="Author")
    author_label.pack()
    global author_entry
    author_entry = tk.Entry(add_frame)
    author_entry.pack()

    publisher_label = tk.Label(add_frame, text="Publisher")
    publisher_label.pack()
    global publisher_entry
    publisher_entry = tk.Entry(add_frame)
    publisher_entry.pack()

    price_label = tk.Label(add_frame, text="Price")
    price_label.pack()
    global price_entry
    price_entry = tk.Entry(add_frame)
    price_entry.pack()

    availability_label = tk.Label(add_frame, text="Availability")
    availability_label.pack()
    global availability_entry
    availability_entry = tk.Entry(add_frame)
    availability_entry.pack()

    # create a button to add a book to the database
    add_button = tk.Button(add_frame, text="Add Book", command=lambda: add_book(title_entry.get(), author_entry.get(), publisher_entry.get(), price_entry.get(), availability_entry.get(), title_entry, author_entry, publisher_entry, price_entry, availability_entry, book_listbox))
    add_button.pack()

    # create a button to clear a selected book
    clear_button = tk.Button(admin_window, text="Clear Selected Book", command=lambda: clear_book(book_listbox))
    clear_button.pack()

    # create a button to show the orders
    show_orders_button = tk.Button(admin_window, text="Show Orders", command=show_orders)
    show_orders_button.pack()

    # create a button to display the users dictionary
    users_button = tk.Button(admin_window, text="View Users", command=show_users)
    users_button.pack()

    # close the connection to the database
    cursor.close()
    conn.close()

    admin_window.mainloop()


def show_orders():
    # connect to orders database
    conn_orders = sqlite3.connect("orders.db")
    cursor_orders = conn_orders.cursor()

    # create the orders window
    orders_window = tk.Tk()
    orders_window.title("Orders")
    orders_window.geometry("400x400")

    # create a label for the order catalog
    catalog_label = tk.Label(orders_window, text="Order Catalog")
    catalog_label.pack()

    # create the orders Treeview
    orders_treeview = ttk.Treeview(orders_window, columns=("Num Books", "Total Price"))
    orders_treeview.pack()

    # define the columns and headings for the Treeview
    orders_treeview.heading("Num Books", text="Num Books")
    orders_treeview.heading("Total Price", text="Total Price")

    # retrieve the orders from the database
    cursor_orders.execute("SELECT num_books, total_price FROM orders")
    orders = cursor_orders.fetchall()

    # add the orders to the Treeview
    for order in orders:
        orders_treeview.insert("", tk.END, values=(order[0], order[1]))

    # close the connection to the database
    cursor_orders.close()
    conn_orders.close()

    orders_window.mainloop()


def show_users():
    # connect to the users database
    conn_users = sqlite3.connect("users.db")
    cursor_users = conn_users.cursor()

    # retrieve the usernames and passwords from the users table
    query = "SELECT username, password FROM users"
    cursor_users.execute(query)
    users_data = cursor_users.fetchall()

    # create the users window
    users_window = tk.Tk()
    users_window.title("Users")

    # create a frame for the Treeview
    tree_frame = tk.Frame(users_window)
    tree_frame.pack()

    # create the Treeview
    user_treeview = ttk.Treeview(tree_frame, columns=("Username", "Password"), show="headings")
    user_treeview.pack(side="left")

    # add horizontal scrollbar
    scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=user_treeview.xview)
    scrollbar_x.pack(side="bottom", fill="x")
    user_treeview.configure(xscrollcommand=scrollbar_x.set)

    # add vertical scrollbar
    scrollbar_y = ttk.Scrollbar(users_window, orient="vertical", command=user_treeview.yview)
    scrollbar_y.pack(side="right", fill="y")
    user_treeview.configure(yscrollcommand=scrollbar_y.set)

    # define the columns and headings for the Treeview
    user_treeview.heading("Username", text="Username")
    user_treeview.heading("Password", text="Password")

    # iterate through the users and add them to the Treeview
    for user in users_data:
        username = user[0]
        password = user[1]
        user_treeview.insert("", tk.END, values=(username, password))

    # create a frame for the delete button
    delete_frame = tk.Frame(users_window)
    delete_frame.pack()

    # create the delete button and pack it into the delete frame
    delete_button = tk.Button(delete_frame, text="Delete User", command=lambda: delete_user(user_treeview, conn_users, cursor_users))
    delete_button.pack()

    # run the users window
    users_window.mainloop()

    # close the connection to the users database
    cursor_users.close()
    conn_users.close()


def delete_user(user_treeview, conn_users, cursor_users):
    # get the selected item(s) from the Treeview
    selection = user_treeview.selection()

    # iterate through the selection and delete the users from the database
    for item in selection:
        username = user_treeview.item(item, "values")[0]
        query = f"DELETE FROM users WHERE username='{username}'"
        cursor_users.execute(query)

    # commit the changes to the database
    conn_users.commit()

    # delete the selected item(s) from the Treeview
    for item in selection:
        user_treeview.delete(item)


def update_book_listbox(book_listbox, filter_entry=None):
    # clear the book catalog listbox
    book_listbox.delete(0, tk.END)

    # retrieve the books from the database
    conn = sqlite3.connect("bookstore.db")
    cursor = conn.cursor()
    if filter_entry:
        query = "SELECT * FROM books WHERE title LIKE ?"
        cursor.execute(query, ('%' + filter_entry + '%',))
    else:
        cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    # add the books to the listbox
    for book in books:
        book_listbox.insert(tk.END, f"{book[1]} by {book[2]} ({book[4]:.2f} USD) - {book[5]} available")

    # close the connection to the database
    cursor.close()
    conn.close()


def add_book(title, author, publisher, price, availability, title_entry, author_entry, publisher_entry, price_entry, availability_entry, book_listbox):
    # check if any of the entries are empty
    if not all((title, author, publisher, price, availability)):
        messagebox.showerror("Error", "Please fill in all fields")
        return

    # check if the price and availability are valid numbers
    try:
        price = float(price)
        availability = int(availability)
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid price and availability")
        return

    conn = sqlite3.connect("bookstore.db")
    cursor = conn.cursor()
    query = "INSERT INTO books (title, author, publisher, price, availability) VALUES (?, ?, ?, ?, ?)"
    cursor.execute(query, (title, author, publisher, price, availability))
    conn.commit()
    cursor.close()
    conn.close()

    # clear the add book form
    title_entry.delete(0, tk.END)
    author_entry.delete(0, tk.END)
    publisher_entry.delete(0, tk.END)
    price_entry.delete(0, tk.END)
    availability_entry.delete(0, tk.END)

    # update the book catalog listbox
    update_book_listbox(book_listbox)
    messagebox.showinfo("Success", "Book added successfully")


def clear_book(book_listbox):
    # get the selected book
    selection = book_listbox.curselection()
    if not selection:
        messagebox.showerror("Error", "Please select a book to clear")
        return

    title = book_listbox.get(selection[0])

    # delete the book from the database
    conn = sqlite3.connect("bookstore.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE title=?", (title,))
    conn.commit()
    cursor.close()
    conn.close()

    # remove the book from the listbox
    book_listbox.delete(selection[0])

    messagebox.showinfo("Success", "Book cleared successfully")


# create the login window
window = tk.Tk()
window.title("Login")
window.geometry("400x300")

# create labels for username and password
username_label = tk.Label(window, text="Username")
username_label.pack()
username_entry = tk.Entry(window)
username_entry.pack()
password_label = tk.Label(window, text="Password")
password_label.pack()
password_entry = tk.Entry(window, show="*")
password_entry.pack()

# create a login button
login_button = tk.Button(window, text="Login", command=login)
login_button.pack()

# create a register button
register_button = tk.Button(window, text="Register", command=register)
register_button.pack()

window.mainloop()