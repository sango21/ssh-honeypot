import argparse
from ssh_honeypot import *

if __name__ == "__main__":
  # first create an instance of an argparse object.
  parser = argparse.ArgumentParser()

  parser.add_argument('-a', '--address', type=str, required=True)
  parser.add_argument('-p', '--port', type=int, required=True)
  parser.add_argument('-u', '--username', type=str)
  parser.add_argument('-pw', '--password', type=str)

  parser.add_argument('-s', '--ssh', action='store_true')
  
  args = parser.parse_args()

  try:
    if args.ssh:
      print("[-] Running SSH Honeypot...")
      # check if user provides username and/or password. If not, set to None.
      if not args.username:
        username = None
      if not args.password:
        password = None

      honeypot(args.address, args.port, args.username, args.password)

    else:
      print("[!] Choose SSH(--ssh) honeypot.")
  except Exception as err:
    print(f"\n Exiting Honeypot ! {err}\n")