import secrets
import string


def generate_random_string(length=20):
  characters = string.ascii_letters + string.digits
  return ''.join(secrets.choice(characters) for i in range(length))
