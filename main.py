import csv
import re
import bcrypt
import requests
import time
import getpass
import logging

# Constants
USER_CSV = 'regno.csv'
MAX_LOGIN_ATTEMPTS = 5
NASA_API_KEY = 'F9D0hjNJB3jhRlPtccyBNij0FVaAjsGcJ1rXcu80'
LOG_FILE = 'user_activity.log'

# Logging configuration
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

# Function to hash the password
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Function to validate password
def check_password(stored_password, provided_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

# Function to validate email format
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# Function to read users from CSV
def read_users():
    users = {}
    try:
        with open(USER_CSV, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                users[row['email']] = {
                    'password': row['password'],
                    'security_question': row['security_question'],
                    'security_answer': row['security_answer']
                }
    except FileNotFoundError:
        print(f"{USER_CSV} not found!")
    return users

# Function to write users to CSV
def write_users(users):
    with open(USER_CSV, mode='w', newline='') as file:
        fieldnames = ['email', 'password', 'security_question', 'security_answer']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for email, data in users.items():
            writer.writerow({
                'email': email,
                'password': data['password'],
                'security_question': data['security_question'],
                'security_answer': data['security_answer']
            })

# Function to sign up a new user
def signup(users):
    email = input("Enter your email: ")
    if not is_valid_email(email):
        print("Invalid email format.")
        return

    if email in users:
        print("Email already registered.")
        return

    password = getpass.getpass("Enter your password (min 8 characters, 1 special character): ")
    if len(password) >= 8 and re.search(r"[!@#$%^&*]", password):
        security_question = input("Enter a security question (for password recovery): ")
        security_answer = input("Enter the answer to your security question: ")

        users[email] = {
            'password': hash_password(password).decode('utf-8'),
            'security_question': security_question,
            'security_answer': security_answer
        }
        write_users(users)
        print("Signup successful!")
    else:
        print("Password does not meet criteria.")

# Function for login
def login(users):
    attempts = 0
    while attempts < MAX_LOGIN_ATTEMPTS:
        email = input("Enter your email: ")
        if not is_valid_email(email):
            print("Invalid email format.")
            continue

        if email not in users:
            print("Email not found.")
            attempts += 1
            continue
        #Hide password functionality
        password = getpass.getpass("Enter your password: ")
        if check_password(users[email]['password'], password):
            print("Login successful!")
            return True, email
        else:
            print("Incorrect password.")
            attempts += 1

    print("Maximum login attempts reached. Please try again later.")
    return False, None

# Function for password reset
def reset_password(users):
    email = input("Enter your registered email for password reset: ")
    if email not in users:
        print("Email not found.")
        return

    print(f"Security question: {users[email]['security_question']}")
    answer = input("Enter your answer: ")

    if answer.lower() == users[email]['security_answer'].lower():
        new_password = getpass.getpass("Enter your new password (min 8 characters, 1 special character): ")
        if len(new_password) >= 8 and re.search(r"[!@#$%^&*]", new_password):
            users[email]['password'] = hash_password(new_password).decode('utf-8')
            write_users(users)
            logging.info(f"Password reset for user: {email}")
            print("Password reset successful!")
        else:
            print("Password does not meet criteria.")
    else:
        print("Incorrect answer.")
        logging.warning(f"Incorrect security answer for email: {email}")

# Function to fetch API data
def fetch_api_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching data: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None

# Function to fetch NASA NEO data
def fetch_neo_data():
    url = f'https://api.nasa.gov/neo/rest/v1/feed?api_key={NASA_API_KEY}'
    data = fetch_api_data(url)

    if data:
        for date, neos in data['near_earth_objects'].items():
            
            print(f"\nNEO close approach on {date}:")
            
            # Display only the first NEO for each date
            neo = neos[0]
            print(f"Name: {neo['name']}")
            print(f"Close Approach Date: {neo['close_approach_data'][0]['close_approach_date']}")
            print(f"Estimated Diameter (m): {neo['estimated_diameter']['meters']['estimated_diameter_max']}")
            print(f"Velocity (km/h): {neo['close_approach_data'][0]['relative_velocity']['kilometers_per_hour']}")
            print(f"Miss Distance (km): {neo['close_approach_data'][0]['miss_distance']['kilometers']}")
            print(f"Hazardous: {neo['is_potentially_hazardous_asteroid']}")
            
    else:
        print("Failed to fetch NASA NEO data")


# Function to fetch NASA SSD data
def fetch_ssd_data():
    object_name = input("Enter the name or ID of a celestial object (e.g., 'mars', '433', 'halley'): ").lower()
   
    url = f"https://api.le-systeme-solaire.net/rest/bodies/{object_name}"
    data = fetch_api_data(url)  
    
    if data:
        print("\n------Solar System Dynamics Data------")
        
        print(f"Name: {data.get('englishName', 'N/A')}")
        print(f"Object Type: {data.get('bodyType', 'N/A')}")
        
        if 'semimajorAxis' in data:
            print("\nOrbital Elements:")
            print(f"Semi-major axis: {data.get('semimajorAxis', 'N/A')} km")
            print(f"Eccentricity: {data.get('eccentricity', 'N/A')}")
            print(f"Inclination: {data.get('inclination', 'N/A')} degrees")
            print(f"Orbital period: {data.get('sideralOrbit', 'N/A')} days")
        
        print("\nPhysical Parameters:")
        print(f"Diameter: {data.get('meanRadius', 'N/A')} km")
        print(f"Mass: {data.get('mass', {}).get('massValue', 'N/A')} x 10^{data.get('mass', {}).get('massExponent', 'N/A')} kg")
        print(f"Density: {data.get('density', 'N/A')} g/cm³")
        
        print(f"Rotation period: {data.get('sideralRotation', 'N/A')} hours")
        
        if data.get('discoveredBy') or data.get('discoveryDate'):
            print("\n------Discovery Information------")
            print(f"Discovered by: {data.get('discoveredBy', 'N/A')}")
            print(f"Discovery date: {data.get('discoveryDate', 'N/A')}")
        
    else:
        logging.warning(f"No data found for the object: {object_name}")
        print(f"No data found for the object: {object_name}")

# Main application
def main():
    users = read_users()

    while True:
        print("🚀 Hey there, space cadet! Buckle up tight, because we’re about to launch into a universe of infinite possibilities! 🌟")
        print("But hold up... even superheroes need to fill out a *tiny* form before the adventure begins! 📝😎")
        print("\n1. Signup\n2. Login\n3. Reset Password\n4. Exit")
        choice = input("Choose an option: ")

        if choice == '1':
            signup(users)
        elif choice == '2':
            success, email = login(users)
            if success:
                while True:
                    print(f"\nWelcome aboard! Time to unleash your inner space explorer!🚀")
                    print("\n1. Fetch NEO Data\n2. Fetch SSD Data\n3. Logout")
                    action = input("Choose an option: ")
                    if action == '1':
                        fetch_neo_data()
                    elif action == '2':
                        fetch_ssd_data()
                    elif action == '3':
                        print("Logged out successfully.")
                        break
                    else:
                        print("Invalid choice.")
        elif choice == '3':
            reset_password(users)
        elif choice == '4':
            print("Goodbye! Don’t worry, we’ll keep the engine running until you’re back!🚀")
            break
        else:
            print("Invalid choice.")
if __name__ == "__main__":
    main()
