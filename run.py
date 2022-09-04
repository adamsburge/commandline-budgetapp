import gspread
import os
import time
import sys
from google.oauth2.service_account import Credentials
from datetime import datetime
from colorama import init
from colorama import Fore, Style
init()
init(autoreset=True)

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
    print_section_border()
    print(f"{Style.BRIGHT}Commandline BudgetApp Dashboard")
    print_section_border()
    total_budgeted = get_total_budgeted_amount()
    print(f"Your current budgeted amount is {Fore.GREEN} £{total_budgeted} \n")
    print("Current Budget\n")
    get_current_budget()
    print("")
    print(f"{Fore.YELLOW}What would you like to do?")
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
        action = input(f"{Fore.YELLOW}Type the number of the action you would like to perform:\n")
        if validate_home_data(action):
            print(" ")
            print("One second while we get things ready...")
            clear_terminal()
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
        print(" ")


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
    space = " "
    dash = "-"
    for k, v in budget_list.items(): 
        num_1_spacing_amount = 3 - len(str(category_num))
        num_2_spacing_amount = 28 - len(str(k))
        spacing_1_amount = space*num_1_spacing_amount 
        spacing_2_amount = dash*num_2_spacing_amount      
        print(str(category_num) + "." + spacing_1_amount + str(k) + ":" + spacing_2_amount + Fore.GREEN + "£" + str(v))
        category_num += 1


def add_paycheck():
    """
    Receive Paycheck information, validate entries and, if valid, allow the user
    to delegate money to various categories. Then return to the home prompt.
    """
    print_section_border()
    print(f"{Style.BRIGHT}Just a few questions about your paycheck:")
    print_section_border()

    while True:
        paycheck = input(f"{Fore.YELLOW}How much is your paycheck?\n")
        if validate_number_entry(paycheck):
            break

    left_to_delegate = float(paycheck)
    print(" ")
    while True:
        date = input(f"{Fore.YELLOW}When did you receive your paycheck? (DD-MM-YY)\n")
        if validate_date_entry(date):
            break
    print_section_border()

    paycheck_transaction = [float(paycheck), "My Employer", date, "Paycheck"]
    append_transaction_row(paycheck_transaction)

    print(" ")
    print(f"{Style.BRIGHT}Time to delegate the money from this paycheck!\n")
    
    while left_to_delegate != 0:
        print_section_border()
        print(f"{Fore.BLUE}{Style.BRIGHT}To make sure you don't have any unbudgeted money, you must delegate all the paycheck.\n")
        print("Here is how your current budget stands:")
        print(" ")
        get_current_budget()
        print(" ")

        print(f"You have {Fore.GREEN}£{left_to_delegate}{Fore.RESET} left to delegate from your paycheck.\n")
        while True:
            selected_category = input(f"{Fore.YELLOW}Type the number of the category you wish to delegate money to:\n")
            if validate_category_num_entry(selected_category):
                break
        
        print(" ")
        category_name = main.row_values(int(selected_category))[0]
        while True:
            amount_to_delegate = input(f"{Fore.YELLOW}How much would you like to put towards {category_name}?\n")
            if validate_number_entry(amount_to_delegate):
                if validate_delegation_max(amount_to_delegate, left_to_delegate):
                    break
        
        print(" ")
        print(f"Perfect. Adding {Fore.GREEN}£{amount_to_delegate}{Fore.RESET} to {category_name}\n")
        
        initial_category_amount = main.row_values(int(selected_category))[1]
        new_category_amount = float(initial_category_amount) + float(amount_to_delegate)
        main.update_cell(int(selected_category), 2, new_category_amount)
        
        left_to_delegate -= float(amount_to_delegate)

    clear_terminal()
    print_section_border()
    print("You have delegated all your paycheck! Well done! Taking you back to the main menu.")

    home_prompt()


def add_transaction():
    """
    Receives new transaction information, deducts money from appropriate
    budget categories, adds transaction to transaction list.
    """
    print_section_border()
    print(f"{Style.BRIGHT}Just a few questions about your transaction:")
    print_section_border()

    while True:
        transaction = input(f"{Fore.YELLOW}How much is the transaction?\n")
        if validate_number_entry(transaction):
            break
    transaction_amount = float(transaction)
    
    print(" ")
    transaction_institution = input(f"{Fore.YELLOW}Which institution or person received the money?\n")

    while True:
        print(" ")
        transaction_date = input(f"{Fore.YELLOW}When did you make this payment? (DD-MM-YY)\n")
        if validate_date_entry(transaction_date):
            break

    print_section_border()
    print(f"Great! From which category should this {Fore.RED}£{transaction_amount}{Fore.RESET} payment to {transaction_institution} be deducted?\n")
    get_current_budget()
    print(" ")

    while True:
        transaction_selected_category = input(f"{Fore.YELLOW}Type the number of the category this transaction falls under:\n")
        if validate_category_num_entry(transaction_selected_category):
            break
    
    transaction_category_name = main.row_values(int(transaction_selected_category))[0]
    print(" ")
    print(f"Deducting {Fore.RED}£{transaction_amount}{Fore.RESET} {transaction_institution} payment from {transaction_category_name}...")
    initial_category_amount = main.row_values(int(transaction_selected_category))[1]
    new_category_amount = float(initial_category_amount) - transaction_amount
    main.update_cell(int(transaction_selected_category), 2, new_category_amount)
    
    new_transaction_list = [-transaction_amount, transaction_institution, transaction_date, transaction_category_name]
    append_transaction_row(new_transaction_list)

    print_section_border()
    while True:
        print(
"""Would you like to add another transaction?
1. Yes
2. No
"""
        )
        end_of_transaction_decision = input("Type 1 or 2\n")
        if validate_y_n_entry(end_of_transaction_decision):
            break
    if end_of_transaction_decision == '1':
        clear_terminal()
        add_transaction()
    else:
        clear_terminal()
        home_prompt()


def adjust_categories():
    """
    Lets the user select to either add or delete a category
    """
    print(
"""Would you like to add or delete a category?
1. Add
2. Delete
"""
        )
    while True:
        adjust_decision = input(f"{Fore.YELLOW}Type 1 or 2\n")
        if validate_y_n_entry(adjust_decision):
            break
    if adjust_decision == '1':
        clear_terminal()
        add_category()
    else:
        clear_terminal()
        delete_category()


def view_recent_transactions():
    """
    Lets the user request to see a specified amount of recent transactions
    """
    amount_of_transactions = len(transactions.col_values(1)) - 1

    print_section_border()
    print(f"You have {amount_of_transactions} transactions in your transaction list.")
    print_section_border()

    while True:
        transaction_amount_request = input(f"{Fore.YELLOW}How many of the most recent would you like to see?\n")
        if validate_transaction_list_num_entry(transaction_amount_request, amount_of_transactions):
            break
    amounts = transactions.col_values(1)
    institutions = transactions.col_values(2)
    date = transactions.col_values(3)
    category = transactions.col_values(4)

    print_section_border()
    print(f"{Fore.BLUE}Your {transaction_amount_request} most recent transactions are:\n")
    print("   Amount — Institution — Date — Category\n")
    for i in range(int(transaction_amount_request)):
        counter = i + 1
        print(str(counter) + ". £ " + amounts[-counter] + " — " + institutions[-counter] + " — " + date[-counter] + " — " + category[-counter])

    print_section_border()
    print(
"""
Would you like to view more transactions?
1. Yes
2. No
"""
        )
    while True:
        end_of_view_transaction_decision = input(f"{Fore.YELLOW}Type 1 or 2\n")
        if validate_y_n_entry(end_of_view_transaction_decision):
            break
    if end_of_view_transaction_decision == '1':
        clear_terminal()
        view_recent_transactions()
    else:
        clear_terminal()
        home_prompt()


def add_category():
    """
    Adds a category to the the category list. Allows the user to
    select the name and the starting amount
    """
    new_category_name = input(f"{Fore.YELLOW}What is the name of the new category?\n")

    print(" ")
    print(f"Adding a {new_category_name} category to your category list and setting starting amount to £0...")
    new_category_list = [new_category_name, 0]
    main.append_row(new_category_list)
    print_section_border()
    print(
"""Would you like to adjust another category?
1. Yes
2. No
"""
        )
    while True:
        end_of_add_category_decision = input(f"{Fore.YELLOW}Type 1 or 2{Fore.RESET}\n")
        if validate_y_n_entry(end_of_add_category_decision):
            break
    if end_of_add_category_decision == '1':
        clear_terminal()
        adjust_categories()
    else:
        clear_terminal()
        home_prompt()    


def delete_category():
    """
    Allows the user to select the category to delete from the category list.
    Then prompts the user to redelegate the money from that category.
    """
    print(f"{Fore.RESET}Not a problem. Here is a list of your current categories:\n")
    get_current_budget()
    print(" ")
    while True:
        delete_selected_category = input(f"{Fore.YELLOW}Type the number of the category you wish to delete:\n")
        if validate_category_num_entry(delete_selected_category):
            break
    category_to_delete = int(delete_selected_category)

    category_to_delete_name = main.row_values(category_to_delete)[0]
    category_to_delete_amount = float(main.row_values(category_to_delete)[1])

    print(" ")
    print(f"Deleting {category_to_delete_name} category...")
    main.delete_rows(category_to_delete)
    print_section_border()

    print(f"{Fore.BLUE}The {category_to_delete_name} category had {Fore.GREEN}£{category_to_delete_amount}{Fore.BLUE} delegated to it.\n")
    print("You will need to delegate this amount to another category.\n")
    
    while category_to_delete_amount != 0:
        print(f"There is {Fore.GREEN}£{category_to_delete_amount}{Fore.RESET} left to delegate from {category_to_delete_name}. Where do you wish to delegate it?\n")
        while True:
            get_current_budget()
            print(" ")
            delegation_category_input = input(f"{Fore.YELLOW}Type the number of the category you wish to delegate money to:\n")
            if validate_category_num_entry(delegation_category_input):
                break
        
        delegation_category = int(delegation_category_input)
        delegation_category_name = main.row_values(delegation_category)[0]
        original_delegation_category_amount = float(main.row_values(delegation_category)[1])

        while True:
            print(" ")
            print(f"{delegation_category_name} has {Fore.GREEN}£{original_delegation_category_amount}{Fore.RESET}.\n")
            amount_to_delegate_input = input(f"{Fore.YELLOW}How much of the remaining {Fore.GREEN}£{category_to_delete_amount}{Fore.YELLOW} do you wish to put towards {delegation_category_name}?\n")
            if validate_delegation_max(amount_to_delegate_input, category_to_delete_amount):
                break
        amount_to_delegate = float(amount_to_delegate_input)
        print(" ")
        print(f"Adding {Fore.GREEN}£{amount_to_delegate}{Fore.RESET} to {delegation_category_name}...")
        new_delegation_category_amount = amount_to_delegate + original_delegation_category_amount
        main.update_cell(delegation_category, 2, new_delegation_category_amount)
        category_to_delete_amount -= amount_to_delegate
        print_section_border()
    clear_terminal()
    print(f"{Style.BRIGHT}You've delegated all the money from the {category_to_delete_name} category.")
    print_section_border()

    print(
"""
Would you like to adjust another category?
1. Yes
2. No
"""
        )
    while True:
        end_of_add_category_decision = input(f"{Fore.YELLOW}Type 1 or 2\n")
        if validate_y_n_entry(end_of_add_category_decision):
            break
    if end_of_add_category_decision == '1':
        clear_terminal()
        adjust_categories()
    else:
        clear_terminal()
        home_prompt()  


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
            raise ValueError(f"You must enter either 1 or 2. You entered {value}")
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


def print_section_border():
    """
    prints a set of dashes to create a border.
    This print statement tidies up the terminal and
    makes it more readable for the user
    """
    print(" ")
    print("----------------------------------")
    print(" ")


def clear_terminal():
    '''
    Call this function to clear
    the terminal of the last section.
    It resets colorama colors also.
    '''
    os.system('cls' if os.name == 'nt' else 'clear')


def txt_effect(text_to_print):
    '''
    This prints all of the text slowly.
    # '''
    for character in text_to_print:
        sys.stdout.write(character)
        sys.stdout.flush()
        time.sleep(0.04)


def loading_view(text):
    print_section_border()
    print(text + ".")
    print_section_border()
    time.sleep(1)
    clear_terminal()
    print_section_border()
    print(text + "..")
    print_section_border()
    time.sleep(1)
    clear_terminal()
    print_section_border()
    print(text + "...")
    print_section_border()
    time.sleep(1)
    clear_terminal()
    print_section_border()
    clear_terminal()

txt_effect("----------------------------------\n")
print(" ")
txt_effect("Welcome to Commandline BudgetApp\n")
print(" ")
txt_effect("----------------------------------\n")
time.sleep(3.5)
clear_terminal()
loading_view("Loading Dashboard")
home_prompt()
