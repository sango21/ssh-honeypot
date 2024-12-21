# README.md

## SSH Honeypot

This project is a Python-based SSH honeypot designed to log and simulate malicious SSH activity. 

### Features
- Emulates a real SSH environment with an interactive shell.
- Logs login attempts (username and password).
- Captures commands used by intruders during the session.
- Supports multi-threaded handling of connections.

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/honeypy.git
   cd honeypy
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure you have the required RSA key file:
   - Place your `server.key` file in the root directory.

### Usage

Run the honeypot using the command-line interface:

```bash
python honeypy.py -a <IP_ADDRESS> -p <PORT> -s --username <USERNAME> --password <PASSWORD>
```

Example:

```bash
python honeypy.py -a 127.0.0.1 -p 2223 -s --username myuser --password mypass
```

### Files Overview
- `honeypy/ssh_honeypot.py`: Contains the SSH server logic and honeypot implementation.
- `honeypy/honeypy.py`: Entry point for the CLI.
- `server.key`: RSA private key for SSH communication.
