#!/usr/bin/env python3
from getpass import getpass
from passlib.hash import bcrypt

def main():
    pwd = getpass("Enter password to hash: ")
    # cost=10 matches your example; change 'rounds' if you want a different cost
    hash_2y = bcrypt.using(rounds=10, ident="2y").hash(pwd)
    print(hash_2y)

if __name__ == "__main__":
    main()

