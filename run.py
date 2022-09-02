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

sales = SHEET.worksheet('main')

data = sales.get_all_values()

def home_prompt():
    """
    Print the current budget details and 
    ask user which action they would like to perform
    """
    print("Welcome to Commandline BudgetApp\n")
    print(f"Your current budgeted amount is £\n")
    print("Current Budget\n")

home_prompt()