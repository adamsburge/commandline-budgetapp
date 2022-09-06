import gspread
import os
import time
import sys
from google.oauth2.service_account import Credentials
from datetime import datetime, date
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

users_sheet = SHEET.worksheet('users')


def home_prompt(category_worksheet, transactions_worksheet):
    """
    Print the current budget details and 
    ask user which action they would like to perform
    """    
    print(f"{Fore.RESET}----------------------------------\n")
    print(f"{Style.BRIGHT}Commandline BudgetApp Dashboard")
    print_section_border()
    total_budgeted = get_total_budgeted_amount(category_worksheet)
    print(f"Your current budgeted amount is {Fore.GREEN} £{total_budgeted} \n")
    print("Current Budget\n")
    get_current_budget(category_worksheet)
    print("")
    print(f"{Fore.YELLOW}What would you like to do?")
    print(
    """
    1. Add an Income Transaction
    2. Add a Payment Transaction
    3. Redelegate/Move Money Around
    4. View Recent Transactions
    5. Add or Delete Categories
    6. My Bank Balance Doesn't Match the Budgeted Amount
    7. I'm done budgeting
    """
    )
    while True:
        action = input(f"{Fore.YELLOW}Type the number of the action you would like to perform:\n{Fore.RESET}")
        if validate_home_data(action):
            print(" ")
            print("One second while we get things ready...")
            clear_terminal()
            break
    
    if int(action) == 1:
        add_paycheck(category_worksheet, transactions_worksheet)
    elif int(action) == 2:
        add_transaction(category_worksheet, transactions_worksheet)
    elif int(action) == 3:
        redelegate(category_worksheet, transactions_worksheet)
    elif int(action) == 4:
        view_recent_transactions(category_worksheet, transactions_worksheet)
    elif int(action) == 5:
        adjust_categories(category_worksheet, transactions_worksheet)
    elif int(action) == 6:
        clear_terminal()
        print("----------------------------------\n")
        print("We get it. We sometimes forget to budget too...")
        print_section_border()
        time.sleep(2)
        clear_terminal()
        update_balance(category_worksheet)
        home_prompt(category_worksheet, transactions_worksheet)
    else:
        print("----------------------------------\n")
        print(" ")
        print(f"{Style.BRIGHT}Thanks for budgeting! Exiting the Application...")
        print(" ")
        print(" ")
        print("----------------------------------")


def get_total_budgeted_amount(category_worksheet):
    """
    Calculates the total budgeted amount from the budget
    """
    budgeted_amount = category_worksheet.col_values(2)
    column_list = [float(x) for x in budgeted_amount]

    return round(sum(column_list),2) 


def get_current_budget(category_worksheet):
    """
    Gets the values of the categories and their budgeted amounts,
    then prints these values in a comprehensible way for the user.
    """
    categories = category_worksheet.col_values(1)
    amount = category_worksheet.col_values(2)

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


def add_paycheck(category_worksheet, transactions_worksheet):
    """
    Receive Paycheck information, validate entries and, if valid, allow the user
    to delegate money to various categories. Then return to the home prompt.
    """
    print("----------------------------------\n")
    print(f"{Style.BRIGHT}Just a few questions about your income transaction:")
    print_section_border()

    while True:
        paycheck = input(f"{Fore.YELLOW}How much is the income amount?\n")
        if validate_number_entry(paycheck):
            break
    left_to_delegate = float(paycheck)

    print(" ")
    transaction_institution = input(f"{Fore.YELLOW}Who or what institution gave you this income?\n")

    print(" ")
    while True:
        date = input(f"{Fore.YELLOW}When did you receive this income? (DD-MM-YY)\n")
        if validate_date_entry(date):
            break

    paycheck_transaction = [float(paycheck), transaction_institution, date, "Income"]
    append_transaction_row(paycheck_transaction, transactions_worksheet)

    clear_terminal()
    
    
    while left_to_delegate != 0:
        print_section_border()
        print(f"{Style.BRIGHT}Time to delegate the money from this income!")
        print_section_border()
        print(f"{Fore.BLUE}{Style.BRIGHT}To make sure you don't have any unbudgeted money, you must delegate all the paycheck.\n")
        print("Here is how your current budget stands:")
        print(" ")
        get_current_budget(category_worksheet)
        print(" ")

        left_to_delegate = round(float(left_to_delegate), 2)
        print(f"You have {Fore.GREEN}£{left_to_delegate}{Fore.RESET} left to delegate from your paycheck.\n")
        while True:
            selected_category = input(f"{Fore.YELLOW}Type the number of the category you wish to delegate money to:\n")
            if validate_category_num_entry(selected_category, category_worksheet):
                break
        
        print(" ")
        category_name = category_worksheet.row_values(int(selected_category))[0]
        while True:
            amount_to_delegate = input(f"{Fore.YELLOW}How much would you like to put towards {category_name}?\n")
            if validate_number_entry(amount_to_delegate):
                if validate_delegation_max(amount_to_delegate, left_to_delegate):
                    break
        
        rounded_down_amount_to_delegate = round(float(amount_to_delegate), 2)
        print(" ")
        print(f"Perfect. Adding {Fore.GREEN}£{rounded_down_amount_to_delegate}{Fore.RESET} to {category_name}...\n")
        
        initial_category_amount = category_worksheet.row_values(int(selected_category))[1]
        new_category_amount = float(initial_category_amount) + rounded_down_amount_to_delegate
        category_worksheet.update_cell(int(selected_category), 2, new_category_amount)
        
        left_to_delegate -= rounded_down_amount_to_delegate
        time.sleep(1.7)
        clear_terminal()

    clear_terminal()
    print("----------------------------------\n")
    print("You have delegated all your income transaction! Well done!")
    print_section_border()

    while True:
        print(
"""Would you like to add another income transaction?
1. Yes
2. No
"""
        )
        end_of_transaction_decision = input("Type 1 or 2\n")
        if validate_y_n_entry(end_of_transaction_decision):
            break
    if end_of_transaction_decision == '1':
        clear_terminal()
        add_paycheck(category_worksheet, transactions_worksheet)
    else:
        clear_terminal()
        home_prompt(category_worksheet, transactions_worksheet)


def add_transaction(category_worksheet, transactions_worksheet):
    """
    Receives new transaction information, deducts money from appropriate
    budget categories, adds transaction to transaction list.
    """
    print("----------------------------------\n")
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
    transaction_amount = round(float(transaction_amount), 2)
    print_section_border()
    print(f"Great! From which category should this {Fore.RED}£{transaction_amount}{Fore.RESET} payment to {transaction_institution} be deducted?\n")
    get_current_budget(category_worksheet)
    print(" ")

    while True:
        transaction_selected_category = input(f"{Fore.YELLOW}Type the number of the category this transaction falls under:\n")
        if validate_category_num_entry(transaction_selected_category, category_worksheet):
            break
    
    transaction_category_name = category_worksheet.row_values(int(transaction_selected_category))[0]
    print(" ")
    print(f"Deducting {Fore.RED}£{transaction_amount}{Fore.RESET} {transaction_institution} payment from {transaction_category_name}...")
    initial_category_amount = category_worksheet.row_values(int(transaction_selected_category))[1]
    new_category_amount = float(initial_category_amount) - transaction_amount
    category_worksheet.update_cell(int(transaction_selected_category), 2, new_category_amount)
    
    new_transaction_list = [-transaction_amount, transaction_institution, transaction_date, transaction_category_name]
    append_transaction_row(new_transaction_list, transactions_worksheet)

    clear_terminal()
    print("----------------------------------\n")
    print(f"{Style.BRIGHT}Success! Your transaction has been budgeted.")
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
        add_transaction(category_worksheet, transactions_worksheet)
    else:
        clear_terminal()
        home_prompt(category_worksheet, transactions_worksheet)


def redelegate(category_worksheet, transactions_worksheet):
    """
    Allows the user to move money between the various budgeted categories
    """
    print("----------------------------------\n")
    print(f"{Style.BRIGHT}Let's redelegate your money")
    print_section_border()

    print("Here is how your current budget stands:\n")
    get_current_budget(category_worksheet)
    print(" ")

    while True:
        from_category_input = input(f"{Fore.YELLOW}Type the number of the category you wish to move money from:\n")
        if validate_category_num_entry(from_category_input, category_worksheet):
            break
    from_category_name = category_worksheet.row_values(int(from_category_input))[0]
    from_category_amount = category_worksheet.row_values(int(from_category_input))[1]

    while True:
        print(" ")
        to_category_input = input(f"{Fore.YELLOW}Type the number of the category you wish to move money from {from_category_name} towards:\n")
        if validate_category_num_entry(to_category_input, category_worksheet):
            break
    to_category_name = category_worksheet.row_values(int(to_category_input))[0]
    to_category_amount = category_worksheet.row_values(int(to_category_input))[1]

    print(" ")
    print(f"{from_category_name} has {Fore.GREEN}£{from_category_amount}{Fore.RESET} and {Fore.BLUE}{to_category_name}{Fore.RESET} has {Fore.GREEN}£{to_category_amount}{Fore.RESET}.\n")

    while True:
        transfer_amount_input = input(f"{Fore.YELLOW}How much of {Fore.BLUE}{from_category_name}{Fore.RESET}'s {Fore.GREEN}£{from_category_amount}{Fore.YELLOW} would you like to move to the {Fore.BLUE}{to_category_name}{Fore.YELLOW} category?\n")
        if validate_delegation_max(transfer_amount_input, from_category_amount):
            break        
    
    print(f"{Fore.RESET}")
    print(f"{Fore.RESET}Moving your money...")

    transfer_amount_input = round(float(transfer_amount_input), 2)

    new_from_category_amount = float(from_category_amount) - float(transfer_amount_input)
    category_worksheet.update_cell(int(from_category_input), 2, new_from_category_amount)

    new_to_category_amount = float(to_category_amount) + float(transfer_amount_input)
    category_worksheet.update_cell(int(to_category_input), 2, new_to_category_amount)
    
    time.sleep(.7)
    clear_terminal()

    print("----------------------------------\n")
    print(f"{Style.BRIGHT}Success!\n")
    print(f"{Style.NORMAL}{Fore.BLUE}{from_category_name}{Fore.RESET} now has {Fore.GREEN}£{new_from_category_amount}{Fore.RESET}")
    print(f"{Style.NORMAL}{Fore.BLUE}{to_category_name}{Fore.RESET} now has {Fore.GREEN}£{new_to_category_amount}{Fore.RESET}")
    print_section_border()

    get_current_budget(category_worksheet)

    print_section_border()
    while True:
        print(
"""Would you like to move more money?
1. Yes
2. No
"""
        )
        end_of_transaction_decision = input("Type 1 or 2\n")
        if validate_y_n_entry(end_of_transaction_decision):
            break
    if end_of_transaction_decision == '1':
        clear_terminal()
        redelegate(category_worksheet)
    else:
        clear_terminal()
        home_prompt(category_worksheet, transactions_worksheet)


def update_balance(category_worksheet):
    """
    Allows the user to input their current bank balance 
    then prompts them to redelegate or add money so that 
    the budget matches their bank balance.
    """
    print("----------------------------------\n")
    print(f"{Style.BRIGHT}Let's get your budget up to date")
    print_section_border()

    while True:
        bank_balance_input = input(f"{Fore.YELLOW}What is your current bank balance?\n")
        if validate_number_entry(bank_balance_input):
            break

    bank_balance = round(float(bank_balance_input), 2)
    budgeted_amount = float(get_total_budgeted_amount(category_worksheet))

    print(f"{Fore.RESET}")
    if bank_balance > budgeted_amount:
        update_higher_bank_balance(bank_balance, category_worksheet)
    else:
        update_lower_bank_balance(bank_balance, category_worksheet)


def adjust_categories(category_worksheet, transactions_worksheet):
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
    print(f"{Fore.RESET}")
    if adjust_decision == '1':
        clear_terminal()
        add_category(category_worksheet, transactions_worksheet)
    else:
        clear_terminal()
        delete_category(category_worksheet, transactions_worksheet)


def view_recent_transactions(category_worksheet, transactions_worksheet):
    """
    Lets the user request to see a specified amount of recent transactions
    """
    amount_of_transactions = len(transactions_worksheet.col_values(1)) - 1

    print_section_border()
    print(f"You have {amount_of_transactions} transactions in your transaction list.")
    print_section_border()

    while True:
        transaction_amount_request = input(f"{Fore.YELLOW}How many of the most recent would you like to see?\n")
        if validate_transaction_list_num_entry(transaction_amount_request, amount_of_transactions):
            break
    amounts = transactions_worksheet.col_values(1)
    institutions = transactions_worksheet.col_values(2)
    date = transactions_worksheet.col_values(3)
    category = transactions_worksheet.col_values(4)

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
        view_recent_transactions(category_worksheet, transactions_worksheet)
    else:
        clear_terminal()
        home_prompt(category_worksheet, transactions_worksheet)


def add_category(category_worksheet, transactions_worksheet):
    """
    Adds a category to the the category list. Allows the user to
    select the name and the starting amount
    """
    print("----------------------------------\n")
    print(f"{Style.BRIGHT}Let's add your new category:")
    print_section_border()

    new_category_name = input(f"{Fore.YELLOW}What is the name of the new category?\n")

    print(" ")
    print(f"Adding a {new_category_name} category to your category list...\n")
    print(f"Setting {new_category_name}'s starting amount to £0...")
    new_category_list = [new_category_name, 0]
    category_worksheet.append_row(new_category_list)
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
        adjust_categories(category_worksheet, transactions_worksheet)
    else:
        clear_terminal()
        home_prompt(category_worksheet, transactions_worksheet)    


def delete_category(category_worksheet, transactions_worksheet):
    """
    Allows the user to select the category to delete from the category list.
    Then prompts the user to redelegate the money from that category.
    """
    print("----------------------------------\n")
    print(f"{Style.BRIGHT}Not a problem. Let's find the category you want to delete:")
    print_section_border()
    
    print(f"{Fore.RESET}Here is a list of your current categories:\n")
    get_current_budget(category_worksheet)
    print(" ")
    while True:
        delete_selected_category = input(f"{Fore.YELLOW}Type the number of the category you wish to delete:\n")
        if validate_category_num_entry(delete_selected_category, category_worksheet):
            break
    category_to_delete = int(delete_selected_category)

    category_to_delete_name = category_worksheet.row_values(category_to_delete)[0]
    category_to_delete_amount = float(category_worksheet.row_values(category_to_delete)[1])

    clear_terminal()
    print(f"{Fore.RESET}----------------------------------\n")
    print(f"Deleting {category_to_delete_name} category...")
    print_section_border()
    category_worksheet.delete_rows(category_to_delete)
    

    category_to_delete_amount = round(float(category_to_delete_amount), 2)
    print(f"{Fore.BLUE}The {category_to_delete_name} category had {Fore.GREEN}£{category_to_delete_amount}{Fore.BLUE} delegated to it.\n")
    print("You will need to delegate this amount to another category.\n")
    
    while_count = 0
    while category_to_delete_amount != 0:
        if while_count > 0:
            clear_terminal()
            print(f"{Fore.RESET}----------------------------------\n")
            print(f"{Fore.GREEN}£{amount_to_delegate}{Fore.RESET} Added to {delegation_category_name}")
            print_section_border()
        category_to_delete_amount = round(float(category_to_delete_amount), 2)
        print(f"There is {Fore.GREEN}£{category_to_delete_amount}{Fore.RESET} left to delegate from {category_to_delete_name}. Where do you wish to delegate it?\n")
        while True:
            get_current_budget(category_worksheet)
            print(" ")
            delegation_category_input = input(f"{Fore.YELLOW}Type the number of the category you wish to delegate money to:\n")
            if validate_category_num_entry(delegation_category_input, category_worksheet):
                break
        
        delegation_category = int(delegation_category_input)
        delegation_category_name = category_worksheet.row_values(delegation_category)[0]
        original_delegation_category_amount = float(category_worksheet.row_values(delegation_category)[1])

        while True:
            print(" ")
            print(f"{delegation_category_name} has {Fore.GREEN}£{original_delegation_category_amount}{Fore.RESET}.\n")
            amount_to_delegate_input = input(f"{Fore.YELLOW}How much of the recategory_worksheeting {Fore.GREEN}£{category_to_delete_amount}{Fore.YELLOW} do you wish to put towards {delegation_category_name}?\n")
            if validate_delegation_max(amount_to_delegate_input, category_to_delete_amount):
                break
        amount_to_delegate = round(float(amount_to_delegate_input), 2)
        print(" ")
        print(f"Adding {Fore.GREEN}£{amount_to_delegate}{Fore.RESET} to {delegation_category_name}...")
        new_delegation_category_amount = amount_to_delegate + original_delegation_category_amount
        category_worksheet.update_cell(delegation_category, 2, new_delegation_category_amount)
        category_to_delete_amount -= amount_to_delegate
        time.sleep(2)
        while_count += 1
    clear_terminal()
    print("----------------------------------\n")
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
        print(f"{Fore.RESET}")
        if validate_y_n_entry(end_of_add_category_decision):
            break
    if end_of_add_category_decision == '1':
        clear_terminal()
        adjust_categories(category_worksheet, transactions_worksheet)
    else:
        clear_terminal()
        home_prompt(category_worksheet, transactions_worksheet)  


def update_higher_bank_balance(bank_balance, category_worksheet):
    """
    Tells the user their bank balance is higher than their budget
    Then calculates how much money they have to delegate to make 
    their budgeted amount equal that of their bank account
    """
    clear_terminal()
    print("----------------------------------\n")
    print(f"{Style.BRIGHT}Your bank balance is higher than your budgeted amount.")
    print(f"{Style.BRIGHT}To fix this, you will need to delegate money to your budget.")
    print_section_border()

    budgeted_amount = get_total_budgeted_amount(category_worksheet)
    left_to_delegate = round(bank_balance, 2) - round(budgeted_amount, 2)

    while_count = 0
    while left_to_delegate != 0:
        left_to_delegate = round(float(left_to_delegate), 2)
        if while_count > 0:
            clear_terminal()
            print(f"{Fore.RESET}----------------------------------\n")
            print(f"{Fore.GREEN}£{left_to_delegate}{Fore.RESET} added to {category_name}")
            print_section_border()
        print("Here is how your current budget stands:")
        print(" ")
        get_current_budget(category_worksheet)
        print(" ")
            
        left_to_delegate = round(left_to_delegate, 2)
        print(f"You have {Fore.GREEN}£{left_to_delegate}{Fore.RESET} left to delegate.\n")
        while True:
            selected_category = input(f"{Fore.YELLOW}Type the number of the category you wish to delegate money to:\n")
            if validate_category_num_entry(selected_category, category_worksheet):
                break

        print(" ")
        category_name = category_worksheet.row_values(int(selected_category))[0]
        while True:
            amount_to_delegate = input(f"{Fore.YELLOW}How much would you like to put towards {category_name}?\n")
            if validate_number_entry(amount_to_delegate):
                if validate_delegation_max(amount_to_delegate, left_to_delegate):
                    break
        amount_to_delegate = round(float(amount_to_delegate), 2)

        print(" ")
        print(f"Perfect. Adding {Fore.GREEN}£{amount_to_delegate}{Fore.RESET} to {category_name}...\n")
        
        initial_category_amount = category_worksheet.row_values(int(selected_category))[1]
        new_category_amount = float(initial_category_amount) + float(amount_to_delegate)
        category_worksheet.update_cell(int(selected_category), 2, new_category_amount)
        time.sleep(2)
        
        left_to_delegate -= float(amount_to_delegate)
        while_count += 1
    
    clear_terminal()
    print("----------------------------------\n")
    print("Success! You've finished delegating and your bank balance now matches the budget")
    print_section_border()
    time.sleep(2.5)
    clear_terminal()


def update_lower_bank_balance(bank_balance, category_worksheet):
    """
    Tells the user their bank balance is lower than their budget
    Then prompts them to withdraw money from their budget in order
    to make their budgeted amount equal to that of their bank account
    """
    clear_terminal()
    print("----------------------------------\n")
    print(f"{Style.BRIGHT}Your bank balance is lower than your budgeted amount")
    print(f"{Style.BRIGHT}To fix this, you will need to deduct money from your budgeted categories")
    print_section_border()

    budgeted_amount = get_total_budgeted_amount(category_worksheet)
    left_to_deduct = round(float(budgeted_amount), 2) - round(float(bank_balance), 2)

    while_count = 0
    while left_to_deduct != 0:
        left_to_deduct = round(float(left_to_deduct), 2)
        if while_count > 0:
            clear_terminal()
            print(f"{Fore.RESET}----------------------------------\n")
            print(f"{Fore.RED}£{left_to_deduct}{Fore.RESET} deducted from {category_name}")
            print_section_border()
        print("Here is how your current budget stands:")
        print(" ")
        get_current_budget(category_worksheet)
        print(" ")

        left_to_deduct = round(float(left_to_deduct), 2)
        print(f"You have {Fore.RED}£{left_to_deduct}{Fore.RESET} left to deduct.\n")
        while True:
            selected_category = input(f"{Fore.YELLOW}Type the number of the category you wish to deduct money from:\n")
            if validate_category_num_entry(selected_category, category_worksheet):
                break
        
        print(" ")
        category_name = category_worksheet.row_values(int(selected_category))[0]
        while True:
            amount_to_deduct = input(f"{Fore.YELLOW}How much would you like to deduct from {category_name}?\n")
            if validate_number_entry(amount_to_deduct):
                if validate_delegation_max(amount_to_deduct, left_to_deduct):
                    break
        amount_to_deduct = round(float(amount_to_deduct), 2)

        print(" ")
        print(f"Deducting {Fore.RED}£{amount_to_deduct}{Fore.RESET} from {category_name}\n")
        
        initial_category_amount = category_worksheet.row_values(int(selected_category))[1]
        new_category_amount = float(initial_category_amount) - float(amount_to_deduct)
        category_worksheet.update_cell(int(selected_category), 2, new_category_amount)
        
        left_to_deduct -= float(amount_to_deduct)
        while_count += 1
    
    clear_terminal()
    print("----------------------------------\n")
    print("Success! You've finished deducting money from your categories")
    print("and your bank balance now matches the budget")
    print_section_border()
    time.sleep(2.5)
    clear_terminal()


def validate_home_data(value):
    """
    Validates the user input from the home page. 
    """
    try:
        if int(value) > 7:
            raise ValueError(f"You must enter a {Fore.BLUE}number{Fore.RESET} between {Fore.BLUE}1{Fore.RESET} and {Fore.BLUE}5{Fore.RESET}. You entered {Fore.RED}{value}{Fore.RESET}.")
    except ValueError as e:
        print(" ")
        print(f"Invalid entry: {e}\n")
        return False
    return True


def validate_number_entry(value):
    """
    Validate entries that need a number
    """
    try:
        if float(value) < .01:
            raise ValueError(f"You must enter a {Fore.BLUE}number greater than 1{Fore.RESET}. You entered {Fore.RED}{value}{Fore.RESET}.")
    except ValueError as e:
        print(" ")
        print(f"Invalid entry: {e}\n")
        return False
    return True


def validate_category_num_entry(value, category_worksheet):
    """
    Used to validate whether an input entry exceeds the number of budget categories.
    """
    entry_amount = len(category_worksheet.col_values(1))
    try:
        if int(value) > int(entry_amount):
            raise ValueError(f"You must enter a {Fore.BLUE}number{Fore.RESET} between {Fore.BLUE}1{Fore.RESET} and {Fore.BLUE}{entry_amount}{Fore.RESET}. You entered {Fore.RED}{value}{Fore.RESET}")
    except ValueError as e:
        print(" ")
        print(f"Invalid entry: {e}.\n")
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
            raise ValueError(f"You must enter a {Fore.BLUE}number{Fore.RESET} between {Fore.BLUE}1{Fore.RESET} and {Fore.BLUE}{max}{Fore.RESET}. You entered {Fore.RED}{value}{Fore.RESET}")
    except ValueError as e:
        print(" ")
        print(f"Invalid entry: {e}.\n")
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
        print(" ")
        print(f"{Fore.RED}{value}{Fore.RESET} is not formated properly.\n")
        return False


def validate_y_n_entry(value):
    """
    Validates any inputs which require yes or no answers
    """
    try:
        if value not in ["1", "2"]:
            raise ValueError(f"You must enter either {Fore.BLUE}1{Fore.RESET} or {Fore.BLUE}2{Fore.RESET}. You entered {Fore.RED}{value}{Fore.RESET}")
    except ValueError as e:
        print(" ")
        print(f"Invalid entry: {e}.\n")
        return False
    return True


def validate_transaction_list_num_entry(value, max):
    """
    Used to validate whether an input entry exceeds the number of transaction list items.
    """
    try:
        if int(value) > int(max):
            raise ValueError(f"You must enter a {Fore.BLUE}number{Fore.RESET} between {Fore.BLUE}1{Fore.RESET} and {Fore.BLUE}{max}{Fore.RESET}. You entered {Fore.RED}{value}{Fore.RESET}\n")
    except ValueError as e:
        print(" ")
        print(f"Invalid entry: {e}.\n")
        return False
    return True


def append_transaction_row(value, transactions_worksheet):
    """
    Append a row to the transaction list
    """
    transactions_worksheet.append_row(value)


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
        time.sleep(0.03)


def startup_view():
    """
    Playsw the startup welcome effect
    """
    clear_terminal()
    txt_effect("----------------------------------\n")
    print(" ")
    txt_effect("Welcome to Commandline BudgetApp\n")
    print(" ")
    txt_effect("----------------------------------\n")
    time.sleep(1.7)

def set_up_new_budget():
    """
    Guides the user through a process to set up a new budget
    """
    print(f"{Fore.RESET}----------------------------------\n")
    print(f"{Style.BRIGHT}Let's get your new budget set up")
    print_section_border()
    print("Here is our preset budget:")
    print(
    f"""
1.  Rent:------------------------{Fore.GREEN}£0{Fore.RESET}
2.  Utilities:-------------------{Fore.GREEN}£0{Fore.RESET}
3.  Phone Bill:------------------{Fore.GREEN}£0{Fore.RESET}
4.  Insurance:-------------------{Fore.GREEN}£0{Fore.RESET}
5.  Debt:------------------------{Fore.GREEN}£0{Fore.RESET}
6.  Retirement:------------------{Fore.GREEN}£0{Fore.RESET}
7.  Groceries:-------------------{Fore.GREEN}£0{Fore.RESET}
8.  Transportation:--------------{Fore.GREEN}£0{Fore.RESET}
9.  Entertainment:---------------{Fore.GREEN}£0{Fore.RESET}
10. Travel:----------------------{Fore.GREEN}£0{Fore.RESET}
11. Miscellaneous:---------------{Fore.GREEN}£0{Fore.RESET}
12. Spending Money:--------------{Fore.GREEN}£0{Fore.RESET}
"""
        )
    print(f"{Fore.BLUE}Would you like to use the preset budget or build your own?{Fore.RESET}\n")
    print("(Both will allow you to further adjust your categories categories after the setup)")
    print(
    """
1. I'll use the preset
2. I want to build my own
"""
        )
    while True:
        preset_or_build = input(f"{Fore.YELLOW}Type 1 or 2\n")
        if validate_y_n_entry(preset_or_build):
            break
    if preset_or_build == '1':
        clear_terminal()
        print(f"{Fore.RESET}----------------------------------\n")
        print(f"{Style.BRIGHT}Setting up your budget...")
        print_section_border()
        time.sleep(2)
        category_worksheet.clear()
        num_of_rows = int(transactions_worksheet.row_count)
        if num_of_rows > 1:
            transactions_worksheet.delete_rows(2, num_of_rows)
        clear_terminal()
        set_up_preset_budget()
        add_money_to_new_budget()
    else:
        category_worksheet.clear()
        num_of_rows = int(transactions_worksheet.row_count)
        if num_of_rows > 1:
            transactions_worksheet.delete_rows(2, num_of_rows)
        clear_terminal()
        build_new_budget()
        add_money_to_new_budget()


def set_up_preset_budget():
    """
    Fills the budget spreadsheet with preset data
    """
    preset_categories = [["Rent", 0], ["Utilities", 0], ["Phone Bill", 0], ["Insurance", 0], ["Debt", 0], ["Retirement", 0], ["Groceries", 0], ["Transportation", 0], ["Entertainment", 0], ["Travel", 0], ["Miscellaneous", 0], ["Spending Money", 0]]
    category_worksheet.append_rows(preset_categories)


def add_money_to_new_budget():
    """
    Prompts the user to input their bank balance and then delegate money
    """
    print(f"{Fore.RESET}----------------------------------\n")
    print(f"{Style.BRIGHT}Let's add some money")
    print_section_border()

    print("Here is your current Budget\n")
    get_current_budget(category_worksheet)

    print(" ")
    print(f"{Fore.BLUE}This budget relies on the budgeted amount matching your bank account balance.\n")

    while True:
        bank_balance = input(f"{Fore.YELLOW}How much is currently in your bank account?\n")
        if validate_number_entry(bank_balance):
            break
    left_to_delegate = float(bank_balance)
    get_today = date.today()
    today = get_today.strftime("%d-%m-%y")

    initial_transaction = [left_to_delegate, "Initial Bank Balance", today, "Income"]
    append_transaction_row(initial_transaction, transactions_worksheet)

    clear_terminal()
    
    
    while left_to_delegate != 0:
        print_section_border()
        print(f"{Style.BRIGHT}Time to delegate the money from this balance")
        print_section_border()
        print(f"{Fore.BLUE}{Style.BRIGHT}To make sure you don't have any unbudgeted money, you must delegate all this balance.\n")
        print("Here is how your current budget stands:")
        print(" ")
        get_current_budget(category_worksheet)
        print(" ")

        left_to_delegate = round(float(left_to_delegate), 2)
        print(f"You have {Fore.GREEN}£{left_to_delegate}{Fore.RESET} left to delegate from your balance.\n")
        while True:
            selected_category = input(f"{Fore.YELLOW}Type the number of the category you wish to delegate money to:\n")
            if validate_category_num_entry(selected_category, category_worksheet):
                break
        
        print(" ")
        category_name = category_worksheet.row_values(int(selected_category))[0]
        while True:
            amount_to_delegate = input(f"{Fore.YELLOW}How much would you like to put towards {category_name}?\n")
            if validate_number_entry(amount_to_delegate):
                if validate_delegation_max(amount_to_delegate, left_to_delegate):
                    break
        
        rounded_down_amount_to_delegate = round(float(amount_to_delegate), 2)
        print(" ")
        print(f"Perfect. Adding {Fore.GREEN}£{rounded_down_amount_to_delegate}{Fore.RESET} to {category_name}...\n")
        
        initial_category_amount = category_worksheet.row_values(int(selected_category))[1]
        new_category_amount = float(initial_category_amount) + rounded_down_amount_to_delegate
        category_worksheet.update_cell(int(selected_category), 2, new_category_amount)
        
        left_to_delegate -= rounded_down_amount_to_delegate
        time.sleep(2)
        clear_terminal()

    clear_terminal()
    print("----------------------------------\n")
    print("You have delegated all your bank balance! Well done!")
    print_section_border()
    time.sleep(2)
    clear_terminal()
    print("----------------------------------\n")
    print("Setting up your dashboard...")
    print_section_border()
    time.sleep(2)
    clear_terminal()
    home_prompt(category_worksheet, transactions_worksheet)

def build_new_budget():
    """
    Allows the user to input their own categories into the cleared budget
    """
    categories_entered = 0
    for i in range(5):
        print(f"{Fore.RESET}----------------------------------\n")
        print(f"{Style.BRIGHT}Great! Let's build your budget")
        print_section_border()

        print(f"{Fore.BLUE}To make things easier later on, you must add at least 5 budget categories right now{Fore.RESET}\n")

        if categories_entered > 0:
            print("Your budget so far:")
            print(" ")
            get_current_budget(category_worksheet)
            print(" ")

        print(f"You have entered {categories_entered} out of 5 required categories\n")

        new_category_name = input(f"{Fore.YELLOW}Type the name of a category to add it\n")

        print(" ")
        print(f"Adding a {new_category_name} category to your category list...\n")
        time.sleep(1)
        print(f"Setting {new_category_name}'s starting amount to £0...")
        time.sleep(1)
        new_category_list = [new_category_name, 0]
        category_worksheet.append_row(new_category_list)
        categories_entered += 1
        clear_terminal()
    
    add_another_category_intro(categories_entered)
    
    


def add_another_category_intro(categories_entered):
    """
    Allows user to add more than 5 categories during build new budget
    """
    category_count = len(category_worksheet.col_values(1))
    print(f"{Fore.RESET}----------------------------------\n")
    print(f"{Style.BRIGHT}Great! You have added {category_count} categories to your budget!")
    print_section_border()
    while True:
        print(
"""Would you like to add another budget category?
1. Yes
2. No
"""
        )
        end_of_transaction_decision = input("Type 1 or 2\n")
        if validate_y_n_entry(end_of_transaction_decision):
            break
    
    if end_of_transaction_decision == '1':
        clear_terminal()
        print(f"{Fore.RESET}----------------------------------\n")
        print(f"{Style.BRIGHT}Great! Let's keep building your budget")
        print_section_border()

        print("Your budget so far:")
        print(" ")
        get_current_budget(category_worksheet)
        print(" ")

        print(f"You have entered {category_count} categories so far\n")

        new_category_name = input(f"{Fore.YELLOW}Type the name of a category to add it\n")

        print(" ")
        print(f"Adding a {new_category_name} category to your category list...\n")
        time.sleep(1)
        print(f"Setting {new_category_name}'s starting amount to £0...")
        time.sleep(1)
        new_category_list = [new_category_name, 0]
        category_worksheet.append_row(new_category_list)
        clear_terminal()
        add_another_category_intro(category_count)
    else:
        clear_terminal()
    

def create_account():
    """
    Allows user to create their own budgeting account
    """
    print(f"{Fore.RESET}----------------------------------\n")
    print(f"{Style.BRIGHT}Let's get your account set up")
    print_section_border()




def startup_prompt():
    """
    Function called at the launch of the program.
    It plays the startup view, then allows the user to either
    keep using their old budget or create a new one
    """
    startup_view()
    print(
    """
What would you like to do?

1. Log in
2. Create an Account
"""
        )
    while True:
        keep_or_start = input(f"{Fore.YELLOW}Type 1 or 2\n")
        if validate_y_n_entry(keep_or_start):
            break
    if keep_or_start == '1':
        clear_terminal()
        print(f"{Fore.RESET}----------------------------------\n")
        print(f"{Style.BRIGHT}Log In")
        print_section_border()

        emails_list = users_sheet.col_values(2)
        usernames_list = users_sheet.col_values(3)
        usernames_email_list = emails_list + usernames_list

        while True:
            username = input(f"{Fore.YELLOW}Enter your username or email:\n")
            if username not in usernames_email_list:
                print(f"{Fore.RESET}")
                print("Sorry, there's no account with that username or email")
                print(" ")
            else:
                break

        username_row = users_sheet.find(username).row
        user_first_name = users_sheet.row_values(username_row)[0]

        while_count = 0
        while True:
            print(" ")
            password = input(f"{Fore.YELLOW}Enter your password:\n")

            if password == users_sheet.row_values(username_row)[3]:
                break
            else:
                print(f"{Fore.RESET} ")
                print("Sorry, that password is incorrect")
                while_count += 1
                if while_count == 3:
                    clear_terminal()
                    print(f"{Fore.RESET}----------------------------------\n")
                    print(f"{Style.BRIGHT}Log In")
                    print_section_border()
                    print("You have failed to log in 3 times\n")
                    print(
    """
Would you like to create an account?

1. Yes
2. No, I'll try my password again
"""
        )
                    while True:
                        password_fail = input(f"{Fore.YELLOW}Type 1 or 2\n")
                        if validate_y_n_entry(password_fail):
                            break
                        if password_fail == 1:
                            print("Let's create your account")


        category_worksheet_name = username + "_"
        transaction_name = username + "_"
        category_worksheet = SHEET.worksheet(category_worksheet_name + 'main')
        transactions_worksheet = SHEET.worksheet(transaction_name + 'transactions')
        time.sleep(1)

        clear_terminal()
        print(f"{Fore.RESET}----------------------------------\n")
        print(f"{Style.BRIGHT}Welcome Back, {user_first_name}. Retrieving your Budget...")
        print_section_border()
        time.sleep(2)
        clear_terminal()
        home_prompt(category_worksheet, transactions_worksheet)
    else:
        clear_terminal()
        create_account()
        set_up_new_budget()

# username = input("Type your username:\n")
# category_worksheet_name = username + "_"
# transaction_name = username + "_"
# 
# SHEET.add_worksheet(category_worksheet_name + "category_worksheet", 1, 2)
# SHEET.add_worksheet(transaction_name + "transactions", 1, 4)
# 
# category_worksheet = SHEET.worksheet(category_worksheet_name + 'category_worksheet')
# transactions_worksheet = SHEET.worksheet(transaction_name + 'transactions')

startup_prompt()
