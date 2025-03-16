import random
from datetime import datetime, timedelta

# List of team members
TEAM_MEMBERS = ["AmiraElSaeed", "MohamedAttay", "AleynaKircali"]

# Define start and end dates for random timestamps
START_DATE = datetime(2025, 2, 1)
END_DATE = datetime(2025, 3, 10)

def assign_random_user():
    """Randomly assigns a user from the team."""
    return random.choice(TEAM_MEMBERS)

def assign_random_timestamp():
    """Generates a random timestamp between Feb 1, 2025, and March 10, 2025."""
    time_delta = END_DATE - START_DATE
    random_days = random.randint(0, time_delta.days)
    random_seconds = random.randint(0, 86400)  # Random seconds in a day
    return (START_DATE + timedelta(days=random_days, seconds=random_seconds)).strftime("%Y-%m-%d %H:%M:%S")