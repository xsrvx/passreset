import requests

def generate_password():
    password = ""

    while len(password) < 10:
        response = requests.get("https://www.dinopass.com/password/simple")
        password = response.text.strip()

    # Capitalize the first letter of the generated password to meet complexity
    password = password[0].upper() + password[1:]

    return password
