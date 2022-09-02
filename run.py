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
    print(f"Your current budgeted amount is £{total_budgeted} \n")
    print("Current Budget\n")

def get_total_budgeted_amount():
    """
    Calculates the total budgeted amount from the budget
    """
    budgeted_amount = main.col_values(2)
    column_list = [int(x) for x in budgeted_amount]

    return sum(column_list)

total_budgeted = get_total_budgeted_amount()

home_prompt()