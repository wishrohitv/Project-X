from modules import bcrypt


# password = b"super secret password"
# Hash a password for the first time, with a randomly-generated salt
# hashed = bcrypt.hashpw(password, bcrypt.gensalt())
# Check that an unhashed password matches one that has previously been hashed
def match_password(password: bytes, hashed: bytes) -> bool:
    if bcrypt.checkpw(password, hashed):
        return True
    else:
        return False


def return_hashed_bytes(password):
    hashedP = bcrypt.hashpw(password, bcrypt.gensalt())
    return hashedP
