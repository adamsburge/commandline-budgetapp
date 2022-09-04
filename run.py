import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
    ]

CREDS = Credentials.from_service_account_file('creds.json')
SCOPED_CREDS = CREDS.with_scopes(SCOPE)
GSPREAD_CLIENT = gspread.authorize(SCOPED_CREDS)
SHEET = GSPREAD_CLIENT.open('commandline-budgetapp')

main = SHEET.worksheet('main')
transactions = SHEET.worksheet('transactions')


def home_prompt():
    """
    Print the current budget details and 
    ask user which action they would like to perform
    """    
    print("Welcome to Commandline BudgetApp\n")
    total_budgeted = get_total_budgeted_amount()
    print(f"Your current budgeted amount is £{total_budgeted} \n")
    print("Current Budget\n")
    get_current_budget()
    print("")
    print("What would you like to do?")
    print(
    """
    1. Add a Paycheck
    2. Add a Transaction
    3. Adjust Categories
    4. View Recent Transactions
    5. I'm done budgeting
    """
    )
    while True:
        action = input("Type the number of the action you would like to perform:\n")
        if validate_home_data(action):
            print("One second while we get things ready\n")
            break
    
    if int(action) == 1:
        add_paycheck()
    elif int(action) == 2:
        add_transaction()
    elif int(action) == 3:
        adjust_categories()
    elif int(action) == 4:
        view_recent_transactions()
    else:
        print("Thanks for budgeting! Exiting the Application...")


def get_total_budgeted_amount():
    """
    Calculates the total budgeted amount from the budget
    """
    budgeted_amount = main.col_values(2)
    column_list = [float(x) for x in budgeted_amount]

    return sum(column_list)


def get_current_budget():
    """
    Gets the values of the categories and their budgeted amounts,
    then prints these values in a comprehensible way for the user.
    """
    categories = main.col_values(1)
    amount = main.col_values(2)

    budget_list = {category: amount for category, amount in zip(categories, amount)}
    category_num = 1
    for k, v in budget_list.items():        
        print(str(category_num) + ". " + str(k) + ": £" + str(v))
        category_num += 1


def add_paycheck():
    """
    Receive Paycheck information, validate entries and, if valid, allow the user
    to delegate money to various categories. Then return to the home prompt.
    """
    while True:
        paycheck = input("How much is your paycheck?\n")
        if validate_number_entry(paycheck):
            break

    left_to_delegate = float(paycheck)

    while True:
        date = input("When did you receive your paycheck? (DD-MM-YY) \n")
        if validate_date_entry(date):
            break

    paycheck_transaction = [float(paycheck), "My Employer", date, "Paycheck"]
    append_transaction_row(paycheck_transaction)

    print("Time to delegate the money from this paycheck!\n")
    
    while left_to_delegate != 0:
        print("To make sure you don't have any unbudgeted money, you must delegate all the paycheck.\n")
        print("Here is how your current budget stands:")
        get_current_budget()
        print(" ")

        while True:
            selected_category = input("Type the number of the category you wish to delegate money to:\n")
            if validate_category_num_entry(selected_category):
                break
        
        print(f"Great! You have £{left_to_delegate} left to delegate from your paycheck.\n")
        category_name = main.row_values(int(selected_category))[0]
        while True:
            amount_to_delegate = input(f"How much would you like to put towards {category_name}?\n")
            if validate_number_entry(amount_to_delegate):
                if validate_delegation_max(amount_to_delegate, left_to_delegate):
                    break
        
        print(f"Perfect. Adding £{amount_to_delegate} to {category_name}\n")
        
        initial_category_amount = main.row_values(int(selected_category))[1]
        new_category_amount = float(initial_category_amount) + float(amount_to_delegate)
        main.update_cell(int(selected_category), 2, new_category_amount)
        
        left_to_delegate -= float(amount_to_delegate)

        print(f"You now have £{left_to_delegate} from your paycheck.\n")
    
    print("You have delegated all your paycheck! Well done! Taking you back to the main menu.")

    home_prompt()


def add_transaction():
    """
    Receives new transaction information, deducts money from appropriate
    budget categories, adds transaction to transaction list.
    """
    while True:
        transaction = input("How much is the transaction?\n")
        if validate_number_entry(transaction):
            break
    transaction_amount = float(transaction)
    
    print(" ")
    transaction_institution = input("Who did you pay?\n")

    while True:
        print(" ")
        transaction_date = input("When did you make this payment? (DD-MM-YY) \n")
        if validate_date_entry(transaction_date):
            break

    print(" ")
    print(f"Great! From which category should this £{transaction_amount} payment to {transaction_institution} be deducted?\n")
    get_current_budget()
    print(" ")

    while True:
        transaction_selected_category = input("Type the number of the category this transaction falls under:\n")
        if validate_category_num_entry(transaction_selected_category):
            break
    
    transaction_category_name = main.row_values(int(transaction_selected_category))[0]
    print(f"Deducting £{transaction_amount} {transaction_institution} payment from {transaction_category_name}...")
    initial_category_amount = main.row_values(int(transaction_selected_category))[1]
    new_category_amount = float(initial_category_amount) - transaction_amount
    main.update_cell(int(transaction_selected_category), 2, new_category_amount)
    
    new_transaction_list = [-transaction_amount, transaction_institution, transaction_date, transaction_category_name]
    append_transaction_row(new_transaction_list)

    print(
"""
Would you like to add another transaction?
1. Yes
2. No
"""
        )
    while True:
        end_of_transaction_decision = input("Type 1 or 2\n")
        if validate_y_n_entry(end_of_transaction_decision):
            break
    if end_of_transaction_decision == '1':
        add_transaction()
    else:
        home_prompt()


def adjust_categories():
    """
    Lets the user select to either add or delete a category
    """
    print(
"""
Would you like to add or delete a category?
1. Add
2. Delete
"""
        )
    while True:
        adjust_decision = input("Type 1 or 2\n")
        if validate_y_n_entry(adjust_decision):
            break
    if adjust_decision == '1':
        add_category()
    else:
        delete_category()


def view_recent_transactions():
    """
    Lets the user request to see a specified amount of recent transactions
    """
    amount_of_transactions = len(transactions.col_values(1)) - 1
    while True:
        transaction_amount_request = input(f"You have {amount_of_transactions} transactions listed. How many of the most recent would you like to see?\n")
        if validate_transaction_list_num_entry(transaction_amount_request, amount_of_transactions):
            break
    amounts = transactions.col_values(1)
    institutions = transactions.col_values(2)
    date = transactions.col_values(3)
    category = transactions.col_values(4)

    print(f"Your {transaction_amount_request} most recent transactions are:\n")
    print("   Amount — Institution — Date — Category\n")
    for i in range(int(transaction_amount_request)):
        counter = i + 1
        print(str(counter) + ". £ " + amounts[-counter] + " — " + institutions[-counter] + " — " + date[-counter] + " — " + category[-counter])

    print(
"""
Would you like to view more transactions?
1. Yes
2. No
"""
        )
    while True:
        end_of_view_transaction_decision = input("Type 1 or 2\n")
        if validate_y_n_entry(end_of_view_transaction_decision):
            break
    if end_of_view_transaction_decision == '1':
        view_recent_transactions()
    else:
        home_prompt()


def add_category():
    """
    Adds a category to the the category list. Allows the user to
    select the name and the starting amount
    """
    new_category_name = input("What is the name of the new category?\n")
    while True:
        new_amount = input("How much money should this category start with?\n")
        if validate_number_entry(new_amount):
            break
    new_category_amount = float(new_amount)

    print(f"Adding a {new_category_name} category to your category list with a starting amount of £{new_amount}...\n")
    new_category_list = [new_category_name, new_category_amount]
    main.append_row(new_category_list)

    print(
"""
Would you like to adjust another category?
1. Yes
2. No
"""
        )
    while True:
        end_of_add_category_decision = input("Type 1 or 2\n")
        if validate_y_n_entry(end_of_add_category_decision):
            break
    if end_of_add_category_decision == '1':
        adjust_categories()
    else:
        home_prompt()    


def delete_category():
    """
    Allows the user to select the category to delete from the category list.
    Then prompts the user to redelegate the money from that category.
    """
    print("Not a problem. Here is a list of your current categories:\n")
    get_current_budget()
    while True:
        delete_selected_category = input("Type the number of the category you wish to delete:\n")
        if validate_category_num_entry(delete_selected_category):
            break
    category_to_delete = int(delete_selected_category)

    category_to_delete_name = main.row_values(category_to_delete)[0]
    category_to_delete_amount = float(main.row_values(category_to_delete)[1])

    print(" ")
    print(f"Deleting {category_to_delete_name} category...\n")
    main.delete_rows(category_to_delete)

    print(f"The {category_to_delete_name} category had £{category_to_delete_amount} delegated to it.\n")
    print("You will need to delegate this amount to another category.\n")
    print("Where do you wish to delegate it?/n")
    get_current_budget()

    


def validate_home_data(value):
    """
    Validates the user input from the home page. 
    """
    try:
        if int(value) > 5:
            raise ValueError(f"You must enter a number between 1 and 5. You entered {value}")
    except ValueError as e:
        print(f"Invalid entry: {e}, please type a number.")
        return False
    return True


def validate_number_entry(value):
    """
    Validate entries that need a number
    """
    try:
        if float(value) < 1:
            raise ValueError(f"You must enter a number greater than 1. You entered {value}")
    except ValueError as e:
        print(f"Invalid entry: {e}, please type a number.")
        return False
    return True


def validate_category_num_entry(value):
    """
    Used to validate whether an input entry exceeds the number of budget categories.
    """
    entry_amount = len(main.col_values(1))
    try:
        if int(value) > int(entry_amount):
            raise ValueError(f"You must enter a number between 1 and {entry_amount}. You entered {value}")
    except ValueError as e:
        print(f"Invalid entry: {e}, please type a number.")
        return False
    return True


def validate_delegation_max(value, max):
    """
    Validates whether a one number is greater than another.
    Used in the paycheck function make sure delegation entries
    are not larger than the paycheck.
    """
    try:
        if float(value) > float(max):
            raise ValueError(f"You must enter a number between 1 and {max}. You entered {value}")
    except ValueError as e:
        print(f"Invalid entry: {e}, please type a number.")
        return False
    return True


def validate_date_entry(value):
    """
    Validate that entries requesting dates are formated correctly
    """
    try:
        if value != datetime.strptime(value, "%d-%m-%y").strftime('%d-%m-%y'):
            raise ValueError
        return True
    except ValueError:
        print("")
        print(f"{value} is not formated properly.\n")
        return False


def validate_y_n_entry(value):
    """
    Validates any inputs which require yes or no answers
    """
    try:
        if int(value) > 2:
            raise ValueError(f"You must enter either 1 (yes) or 2 (no). You entered {value}")
    except ValueError as e:
        print(f"Invalid entry: {e}, please type a number.")
        return False
    return True


def validate_transaction_list_num_entry(value, max):
    """
    Used to validate whether an input entry exceeds the number of transaction list items.
    """
    try:
        if int(value) > int(max):
            raise ValueError(f"You must enter a number between 1 and {max}. You entered {value}\n")
    except ValueError as e:
        print(f"Invalid entry: {e}, please type a number.")
        return False
    return True


def append_transaction_row(value):
    """
    Append a row to the transaction list
    """
    transactions.append_row(value)


home_prompt()
