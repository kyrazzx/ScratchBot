# ScratchBot
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)

ScratchBot that interact with project comments and execute commands.

**Current version:** v1.4.0

---

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/kyrazzx/ScratchBot.git
cd ScratchBot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Create the `.env` File
This file stores your secret credentials. Create a file named `.env` in the project root and add the following:
```env
# Your bot's Scratch account credentials
BOTUSERNAME="YourBotUsername"
BOTPASSWORD="YourBotPassword"

# The ID of the project where the bot will read comments
BOTPROJECT="YourProjectID"

# (Optional) A comma-separated list of admin usernames
ADMIN_USERNAMES="apopo13,githubtest"
```

### 5. Run the Bot
Once everything is configured, you can start the bot:
```bash
python main.py
```

---

## Commands

| Command | Description | Access |
|---|---|---|
| `+help` | Displays the list of available commands. | Public |
| `+follow` | The bot will follow the user who sent the command. | Public (Cooldown) |
| `+gift <username>` | The bot will follow `<username>`. Each user can only gift once. | Public (Cooldown) |
| `+resetgift <username>` | Resets the gift status for `<username>`, allowing them to gift again. | **Admin Only** |

---

## Demo
To try the **latest** demo project available, click [here](https://scratch.mit.edu/projects/1187767540/)!

---

## Latest test

The **latest** version of this script with the **latest** patchs was the **11/06/25** at **12:03**.

Note: Seems stable. May cause unexpected errors.

---

## WARNING!
This bot interacts with Scratch in ways that may be against the **Scratch Terms of Use**. Using this bot could potentially get your bot account **BANNED or DELETED**.

Use this script at your own risk. The creator is not responsible for any consequences.

---

## License
This project is licensed under the MIT License.

---

### Feel free to contribute to make this project better