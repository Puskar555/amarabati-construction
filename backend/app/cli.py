"""Provision named administrators without any baked-in default password."""
import argparse
import getpass
import os
from .db import connection, one
from .security import hash_password, totp_secret, encrypt_secret

def main():
    parser=argparse.ArgumentParser(description='Create named admin; save TOTP secret securely in authenticator app')
    parser.add_argument('--email',required=True)
    parser.add_argument('--name',required=True)
    parser.add_argument('--role',choices=['super_admin','regional_admin'],required=True)
    parser.add_argument('--region',default='')
    args=parser.parse_args()
    if args.role=='regional_admin' and not args.region:parser.error('Regional admin requires --region')
    key=os.getenv('TOTP_ENCRYPTION_KEY','')
    if not key:parser.error('TOTP_ENCRYPTION_KEY must be configured')
    password=getpass.getpass('Choose a strong admin password (minimum 12 characters): ')
    if len(password)<12:parser.error('Password too short')
    secret=totp_secret()
    with connection() as db:
        if one(db,'SELECT id FROM users WHERE email=%s',(args.email.lower(),)):parser.error('Email already exists')
        row=one(db,"""INSERT INTO users(name,email,password_hash,role,region,totp_secret_enc)
          VALUES(%s,%s,%s,%s,%s,%s) RETURNING id""",
          (args.name,args.email.lower(),hash_password(password),args.role,args.region,encrypt_secret(secret,key)))
    print('\nAdmin created:',row['id'])
    print('Set up an authenticator app with this one-time setup secret:')
    print(secret)
    print('Store this secret safely. Do not copy it into tickets, source control or logs.')
if __name__=='__main__':main()
