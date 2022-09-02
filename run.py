import gspread
from google.oauth2.service_account import Credentials

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
        print("You picked 2!")
    elif int(action) == 3:
        print("You picked 3!")
    elif int(action) == 4:
        print("You picked 4!")
    else:
        print("You picked 5!")

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
    try:
        if float(value) < 1:
            raise ValueError(f"You must enter a number greater than 1. You entered {value}")
    except ValueError as e:
        print(f"Invalid entry: {e}, please type a number.")
        return False
    return True
    

home_prompt()