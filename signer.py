#! /usr/bin/env python3
from Crypto.PublicKey import RSA
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme
from Crypto.Hash import SHA256
import sys
import binascii

def import_key(keyName):
  with open(f"{keyName}",'rb') as f:
    return RSA.import_key(f.read())

def sign(key, message):
  hashval = SHA256.new(message.encode("utf8"))
  signer = PKCS115_SigScheme(key)
  signature = signer.sign(hashval)
  return binascii.hexlify(signature).decode("utf8")

def verify(pubKey, message, sighex):
  signature = binascii.unhexlify(sighex)
  hashval = SHA256.new(message.encode("utf8"))
  verifier = PKCS115_SigScheme(pubKey)
  try:
    verifier.verify(hashval, signature)
    return True
  except:
    return False

def gen_key(keyName):
  keyPair = RSA.generate(bits=1024)
  pubKey = keyPair.publickey()
  with open(f"{keyName}.pem",'wb') as f:
    f.write(keyPair.export_key('PEM'))
  with open(f"{keyName}.pub",'wb') as f:
    f.write(pubKey.export_key('PEM'))

if __name__ == "__main__":
  if sys.argv[1] == "gen":
    keyName = sys.argv[2]
    print(f"Generating keys {keyName}.pem {keyName}.pub")
    gen_key(keyName)
  elif sys.argv[1] == "sign":
    keyName = sys.argv[2]
    message = sys.argv[3]
    print(sign(import_key(keyName), message))
  elif sys.argv[1] == "verify":
    pubKey = sys.argv[2]
    message = sys.argv[3]
    signature = sys.argv[4]
    print(verify(import_key(pubKey), message,signature))
  else:
    print(f"Unknown command {sys.argv[1]}")
