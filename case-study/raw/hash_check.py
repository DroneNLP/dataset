import os
import hashlib
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--src_dir", default="src/evidence/raw", help="Folder with encrypted logs")
parser.add_argument('--generate', action='store_true', help="Generate hash for the files and store them into JSON.")
parser.add_argument('--verify', action='store_true', help="Generate hash to verify the hash in the JSON file.")


def calculate_file_hash(filepath, algorithm='sha256'):
    """
    Calculates the hash of a file using the specified algorithm.

    Args:
        filepath (str): The path to the file.
        algorithm (str): The hashing algorithm to use (e.g., 'md5', 'sha1', 'sha256').

    Returns:
        str: The hexadecimal representation of the file's hash, or None if an error occurs.
    """
    try:
        # Create a hash object based on the chosen algorithm
        if algorithm == 'md5':
            hasher = hashlib.md5()
        elif algorithm == 'sha1':
            hasher = hashlib.sha1()
        elif algorithm == 'sha256':
            hasher = hashlib.sha256()
        # Add more algorithms as needed
        else:
            print(f"Unsupported algorithm: {algorithm}")
            return None

        # Open the file in binary read mode
        with open(filepath, 'rb') as file:
            # Read the file in chunks and update the hash object
            for chunk in iter(lambda: file.read(4096), b''):  # Read 4KB chunks
                hasher.update(chunk)

        # Return the hexadecimal representation of the hash
        return hasher.hexdigest()

    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def main():
    args = parser.parse_args()
    evidence_files = []
    BASE_DIR = args.src_dir
    for filename in os.listdir(BASE_DIR):
        if filename.endswith(".txt"):
            evidence_files.append(os.path.join(BASE_DIR, filename))
    
    print(evidence_files)

    hash_dict = []
    for file in evidence_files:
        sha256 = calculate_file_hash(file, 'sha256')
        sha1 = calculate_file_hash(file, 'sha1')
        md5 = calculate_file_hash(file, 'md5')
        hash_dict.append({
            'filename': file,
            'md5': md5,
            'sha1': sha1,
            'sha256': sha256,
        })
    
    if args.generate: # save into files
        # Open the file in write mode and use json.dump()
        with open('hash.json', 'w') as f:
            json.dump(hash_dict, f, indent=4) # indent=4 for pretty-printing
    else:   # print hash
        for hash in hash_dict:
            print(f'filename: {hash['filename']}')
            print(f'\tmd5: {hash['md5']}')
            print(f'\tsha1: {hash['sha1']}')
            print(f'\tsha256: {hash['sha256']}')

    
if __name__ == "__main__":
    main()