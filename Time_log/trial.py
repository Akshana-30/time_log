from flask import Flask, request, render_template, redirect, url_for, session
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Necessary for session management

# Connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# Access 'Sheet1' for login/logout records
sheet_1 = client.open("Login_Database").worksheet('Sheet1')
# Access 'Sheet2' for username and password validation
sheet = client.open("Login_Database").worksheet('Sheet2')


# Function to check if the username and password match
def check_user_exists(username, password):
    users = sheet.get_all_records(empty2zero=False, head=1)
    for user in users:
        username_in_sheet = str(user['Username']).strip()
        password_in_sheet = str(user['Password']).strip()

        username_input = str(username).strip()
        password_input = str(password).strip()

        if username_in_sheet == username_input and password_in_sheet == password_input:
            return True
    return False


# Function to record login details in 'Sheet1'
def record_login(username):
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M:%S")

    # Append username, login date, and time, leaving the logout columns empty for now
    sheet_1.append_row([username, current_date, current_time, '', '', '', ''])  # Empty break columns


# Function to record logout details in 'Sheet1'
def record_logout(username):
    current_time = datetime.now().strftime("%H:%M:%S")
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Find the last row with the matching username and no logout time
    records = sheet_1.get_all_records()
    for i, record in enumerate(records):
        if record['Username'] == username and not record['Logout time']:  # Empty logout field
            # Update the logout time in the same row
            sheet_1.update(f'D{i + 2}', [[current_date]])  # Logout date column
            sheet_1.update(f'E{i + 2}', [[current_time]])  # Logout time column
            break


# Function to record the start of a break in 'Sheet1'
def record_break_start(username):
    current_time = datetime.now().strftime("%H:%M:%S")

    # Find the last row with the matching username and no break start time
    records = sheet_1.get_all_records()
    for i, record in enumerate(records):
        if record['Username'] == username and not record['Break start time']:  # Empty break start field
            # Update the break start time in the same row
            sheet_1.update(f'F{i + 2}', [[current_time]])  # Break start time column
            break


# Function to record the end of a break in 'Sheet1'
def record_break_end(username):
    current_time = datetime.now().strftime("%H:%M:%S")

    # Find the last row with the matching username and no break end time
    records = sheet_1.get_all_records()
    for i, record in enumerate(records):
        if record['Username'] == username and not record['Break end time']:  # Empty break end field
            # Update the break end time in the same row
            sheet_1.update(f'G{i + 2}', [[current_time]])  # Break end time column
            break


@app.route('/')
def login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form['username']
    password = request.form['password']

    if check_user_exists(username, password):
        # Record login details
        record_login(username)

        # Initialize break status to 'Start Break' when the user logs in
        session['break_status'] = 'Start Break'

        return render_template('logged_in.html', username=username, break_status=session['break_status'])
    else:
        return "Invalid username or password. Please try again."


@app.route('/logout', methods=['POST'])
def handle_logout():
    username = request.form['username']

    # Record logout details
    record_logout(username)

    # Clear the break status
    session.pop('break_status', None)

    # Redirect back to the login page
    return render_template('login.html')


@app.route('/toggle_break', methods=['POST'])
def toggle_break():
    username = request.form['username']

    # Toggle break status
    if session['break_status'] == 'Start Break':
        # Record the start break time
        record_break_start(username)
        session['break_status'] = 'End Break'
    else:
        # Record the end break time
        record_break_end(username)
        session['break_status'] = 'Start Break'

    return render_template('logged_in.html', username=username, break_status=session['break_status'])


if __name__ == '__main__':
    app.run(debug=True)
