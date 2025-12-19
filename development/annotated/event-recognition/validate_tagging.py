import re
import pandas as pd


def validate_bioes_span(tags):
    if not tags:
        return True, "Valid (empty)"
    
    entity_type = None
    state = 'O'  # Start outside
    for i, tag in enumerate(tags):
        prefix, *suffix = tag.split('-')
        suffix = '-'.join(suffix) if suffix else None
        
        if prefix == 'O':
            if state != 'O' and state != 'E' and state != 'S':
                return False, f"Invalid abrupt end at index {i}"
            state = 'O'
            continue
        
        if suffix not in ['Event', 'NonEvent']:
            return False, f"Invalid entity type '{suffix}' at index {i}"
        
        if entity_type is None:
            entity_type = suffix
        elif entity_type != suffix:
            return False, f"Inconsistent type '{suffix}' (expected '{entity_type}') at index {i}"
        
        if prefix == 'B':
            if state != 'O' and state != 'E' and state != 'S':
                return False, f"Invalid B start after {state} at index {i}"
            state = 'B'
        elif prefix == 'I':
            if state not in ['B', 'I']:
                return False, f"Invalid I without prior B/I at index {i}"
            state = 'I'
        elif prefix == 'E':
            if state not in ['B', 'I']:
                return False, f"Invalid E without prior B/I at index {i}"
            state = 'E'
            entity_type = None  # Reset for next span
        elif prefix == 'S':
            if state != 'O' and state != 'E' and state != 'S':
                return False, f"Invalid S start after {state} at index {i}"
            state = 'S'
            entity_type = None
        else:
            return False, f"Unknown prefix '{prefix}' at index {i}"
    
    # Check if span properly closed
    if state in ['B', 'I']:
        return False, "Unclosed span (missing E)"
    
    return True, "Valid"

def process_conll_file(input_file, log_file):
    with open(input_file, 'r') as f, open(log_file, 'a') as log:
        sentence = []
        line_num = 0
        for line in f:
            line_num += 1
            line = line.strip()
            if not line:  # End of sentence
                if sentence:
                    words, tags = zip(*sentence)
                    is_valid, message = validate_bioes_span(tags)
                    log.write(f"Sentence at line {line_num - len(sentence)}: {' '.join(words)}\n")
                    log.write(f"Tags: {' '.join(tags)}\n")
                    log.write(f"Validation: {message}\n\n")
                    if not is_valid:
                        print(f"Flagged invalid sentence at line {line_num - len(sentence)}: {message}")
                    sentence = []
                continue
            try:
                word, tag = line.split()
                sentence.append((word, tag))
            except ValueError:
                log.write(f"Error parsing line {line_num}: {line}\n")
    
    # Process last sentence if no trailing blank
    if sentence:
        words, tags = zip(*sentence)
        is_valid, message = validate_bioes_span(tags)
        with open(log_file, 'a') as log:
            log.write(f"Sentence at line {line_num - len(sentence) + 1}: {' '.join(words)}\n")
            log.write(f"Tags: {' '.join(tags)}\n")
            log.write(f"Validation: {message}\n\n")
        if not is_valid:
            print(f"Flagged invalid sentence at line {line_num - len(sentence) + 1}: {message}")

def process_csv_file(input_file, log_file):
    dataframe = pd.read_csv(input_file)
    print(dataframe).head(5)
    
    prev_idx = 0
    token_idx = 1
    with open(log_file, 'a') as log:
        for i, row in dataframe.iterrows():
            sentence = []
            if prev_idx != row['sentence_id']:
                if sentence:
                    token_ids, words, tags = zip(*sentence)
                    is_valid, message = validate_bioes_span(tags)
                    log.write(f"Sentence at index {prev_idx}: {' '.join(words)}\n")
                    log.write(f"Tags: {' '.join(tags)}\n")
                    log.write(f"Validation: {message}\n\n")
                    if not is_valid:
                        print(f"Flagged invalid sentence at line {prev_idx}: {message}")
                    sentence = []
                    token_idx = 1

                    # insert the current token
                    word, tag = row['word'], row['tag']
                    sentence.append((token_idx, word, tag))
                    token_idx += 1
                    prev_idx = row['sentence_id']
                continue
            try:
                word, tag = row['word'], row['tag']
                sentence.append((token_idx, word, tag))
                token_idx += 1
                prev_idx = row['sentence_id']
            except ValueError:
                log.write(f"Error parsing at {row['sentence_id']}: {row['word']}\n")
    if sentence:
        token_ids, words, tags = zip(*sentence)
        is_valid, message = validate_bioes_span(tags)
        log.write(f"Sentence at index {prev_idx}: {' '.join(words)}\n")
        log.write(f"Tags: {' '.join(tags)}\n")
        log.write(f"Validation: {message}\n\n")
        if not is_valid:
            print(f"Flagged invalid sentence at line {prev_idx}: {message}")
        sentence = []

def main():
    # Usage
    # process_conll_file('airdata-prediction.conll', 'airdata-corrections_log.md')
    # process_conll_file('vto-lab-prediction.conll', 'vto-lab-corrections_log.md')
    process_csv_file('airdata-prediction.csv', 'airdata-correction-log-1.md')


if __name__ == "__main__":
    main()