import random
import string

# Generate a secure secret key
length = 50
chars = string.ascii_letters + string.digits + string.punctuation
secret_key = ''.join(random.SystemRandom().choice(chars) for _ in range(length))

print("Generated Django SECRET_KEY:")
print(secret_key)

# Save to .env file
with open('.env', 'a') as f:
    f.write(f'\nSECRET_KEY={secret_key}\n')

print("\nSecret key has been saved to .env file.")
