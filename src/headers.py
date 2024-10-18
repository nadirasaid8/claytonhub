from src.agent import generate_random_user_agent

def get_headers(acc_data):
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Init-Data": acc_data,
        "Origin": "https://tonclayton.fun",
        "Priority": "u=1, i",
        "Referer": "https://tonclayton.fun/games/game-stack",
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": generate_random_user_agent(),
    }
