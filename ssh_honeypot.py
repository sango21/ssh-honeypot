# LIBRARIES
import logging
from logging.handlers import RotatingFileHandler 
import socket
import paramiko
import paramiko.transport
import threading

# CONSTANTS
logging_format = logging.Formatter('%(message)s')
SSH_BANNER = "SSH-2.0-MySSHServer_1.0"

host_key = paramiko.RSAKey(filename='server.key')

# LOGGERS AND LOGGING FILES

# audits log (ip add, username, password)
funnel_logger = logging.getLogger('FunnelLogger')
funnel_logger.setLevel(logging.INFO)

# RotatingFileHandler: This handler is useful for preventing large log files by creating backups and rotating the logs as needed.
funnel_handler = RotatingFileHandler('audits.log', maxBytes=2000, backupCount=5)
funnel_handler.setFormatter(logging_format)

funnel_logger.addHandler(funnel_handler)

# creds logger (emulated shell - capture commands used by hacker during honeypot session).
creds_logger = logging.getLogger('CredsLogger')
creds_logger.setLevel(logging.INFO)

creds_handler = RotatingFileHandler('cmd_audits.log', maxBytes=2000, backupCount=5)
creds_handler.setFormatter(logging_format)

creds_logger.addHandler(creds_handler)

# EMULATED SHELL

def emulated_shell(channel, client_ip):
  channel.send(b'corporate-jumpbox2$ ') # send(print) into the shell env.
  command = b"" # listen to receive commands
  while True:
    char = channel.recv(1) # get input from user
    channel.send(char) # print char back to the shell (to emulate a real shell)
    if not char: # if user enters smth that isnt a character.
      channel.close()
           
    command += char
    # emulate some common shell commands.
    if char == b'\r':
      if command.strip() == b'exit':
        response = b'\b Goodbye \n'
        channel.close()
      elif command.strip() == b'pwd':
        response = b'\n' + b'\\usr\\local' + b'\r\n' # '\r'->enter '\n'->new line
        creds_logger.info(f'Command {command.strip()}' + ", executed by " f'{client_ip}')
      elif command.strip() == b'whoami':
        response = b'\n' + b'corpuser1' + b'\r\n'
        creds_logger.info(f'Command {command.strip()}' + ", executed by " f'{client_ip}')
      elif command.strip() == b'ls':
        response = b'\n' + b'jumpbox.conf' + b'\r\n'
        creds_logger.info(f'Command {command.strip()}' + ", executed by " f'{client_ip}')      
      elif command.strip() == b'cat jumpbox.conf':
        response = b'\n' + b'JUMPBOX CONF IS EMPTY!!' + b'\r\n'
        creds_logger.info(f'Command {command.strip()}' + ", executed by " f'{client_ip}')
      else:
        # if user enters any other command, we will just echo what the user entered back to the shell.
        response = b'\n' + bytes(command.strip()) + b'\r\n'
        creds_logger.info(f'Command {command.strip()}' + ", executed by " f'{client_ip}')
      # repopulate the default dialogue box and listen for next command.
      channel.send(response) # print the response into the shell
      channel.send(b'corporate-jumpbox2$ ') 
      command = b"" # reset the command 

# SSH SERVER + SOCKETS

# declare a new class called Server that inherits from paramiko.ServerInterface.
# paramiko.ServerInterface: This is an interface provided by Paramiko that allows you to implement a custom SSH server.
class Server(paramiko.ServerInterface):
  # constructor method of the class.
  def __init__(self, client_ip, input_username=None, input_password=None):
    self.event = threading.Event()
    self.client_ip = client_ip
    self.input_username = input_username
    self.input_password = input_password

  def check_channel_request(self, kind:str, chanid: int) -> int:
    if kind == 'session':
      return paramiko.OPEN_SUCCEEDED

  def get_allowed_auths(self, username):
    return "password"

  def check_auth_password(self, username, password):
    funnel_logger.info(f"Client {self.client_ip} attempted connection with " + f"username: {username}, " + f"password: {password}")
    creds_logger.info(f'{self.client_ip}, {username}, {password}')
    if self.input_username is not None and self.input_password is not None:
      if username == self.input_username and password == self.input_password:
        return paramiko.AUTH_SUCCESSFUL
      else:
        return paramiko.AUTH_FAILED
    else:
      return paramiko.AUTH_SUCCESSFUL

  def check_channel_shell_request(self, channel):
    self.event.set()
    return True
  
  def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
    return True
  
  def check_channel_exec_request(self, channel, command):
    command = str(command)
    return True
 
def client_handle(client, addr, username, password):
  client_ip = addr[0]
  print(f"{client_ip} has connected to ther SErver.")

  try:
    # handle low level ssh session
    transport = paramiko.Transport(client)
    transport.local_version = SSH_BANNER
    server = Server(client_ip= client_ip, input_username=username, input_password=password)

    transport.add_server_key(host_key)
    transport.start_server(server=server)

    channel = transport.accept(100) 
    if channel is None:
      print("No channel was opened.")

    standard_banner = "Welcome to Ubuntu 22.04 LTS (Tengkhar)! \r\n\r\n"
    channel.send(standard_banner)
    emulated_shell(channel, client_ip=client_ip)

  except Exception as error:
    print(error)
    print("!!! ERROR !!!")

  finally:
    try:
      transport.close()
    except Exception as error:
      print(error)
      print("!!! ERROR !!!")

    client.close()

# SSH-based Honeypot
def honeypot(address, port, username, password):
  socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Creates a new socket object to handle network communication.
  socks.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allows the server to reuse the same address and port immediately after the program is closed or restarted.
  socks.bind((address, port)) # Tells the socket to listen on a specific IP address (host) and port (port).

  socks.listen(10) # how many connections we can handle
  print(f"SSH server is listening on port {port}.")

  # build logic that is going to listen for this socket at a particular address and port and accpet a new connection and hand it off to client_handle.
  # Create an infinite loop so the server continuously listens for and handles new client connections.
  while True:
    try: 
      # Wait for a client to connect. When a connection is made:
        # client: Represents the socket connected to the client.
        # addr: The client's address (IP and port).
      client, addr = socks.accept()
      ssh_honeypot_thread = threading.Thread(target=client_handle, args=(client, addr, username, password))
      ssh_honeypot_thread.start()

    except Exception as error:
      print(error)

# honeypot('127.0.0.1', 2223, 'myuser', 'mypass')