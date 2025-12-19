import re
import json
import unicodedata
import pandas as pd
from typing import List, Dict, Any, Union


def normalize_text(text):
    return unicodedata.normalize("NFC", text)


def tokenize_raw_text(text: str):
    """
    Tokenizes a single string into a list of tokens based on spaces
    and punctuation, correctly handling decimals, units, and complex units.
    
    Args:
        text: The input string to tokenize.
    
    Returns:
        A list of tokens.
    """
    # Strip whitespace
    text = normalize_text(text)
    text = text.strip()
    
    # Add period if doesn't end with punctuation
    # if text and text[-1] not in '.!?,':
    #     text += '.'
    
    # Normalize spacing - single spaces between words
    text = re.sub(r'\s+', ' ', text)
    # This regex is updated to include '/' in the list of standalone punctuation.
    # tokens = re.findall(r"\d+(?:\.\d+)?(?:[a-zA-Z\/°]+)?|\d+(?:\.\d+)?|[\w']+|[.,!?;:()\[\]\/-]+", text)
    # tokens = re.findall(r"\d+(?:\.\d+)?(?:[a-zA-Z\/°]+)?|[\w']+|[.,!?;:()\[\]\/-]", text)
    # tokens = re.findall(r"\d+(?:\.\d+)?(?:[a-zA-Z\/°]+)?|[\w'()-]+|[.,!?;:]", text)
    # tokens = re.findall(r"\d+(?:\.\d+)?(?:[a-zA-Z\/°]+)?\)?|[\w'()-]+|[.,!?;:]", text)
    tokens = re.findall(r"[a-zA-Z0-9\/°'()_-]+|[.,!?;:]", text)

    return tokens


def spacy_to_conll(annotation: List[Union[str, Dict[str, Any]]]) -> str:
    """
    Converts a single SpaCy-style annotation to a CoNLL formatted string
    using a custom pre-tokenizer and the BIOES tagging scheme.

    Args:
        annotation: A list containing the text and a dictionary of entities,
                    e.g., ["text", {"entities": [[start, end, "LABEL"]]}]

    Returns:
        A CoNLL formatted string for the annotation.
    """
    
    # --- 1. Custom Pre-tokenizer ---
    # def pre_tokenize(text: str) -> List[str]:
    #     processed_text = re.sub(r'([.,:])', r' \1 ', text)
    #     return processed_text.split()

    raw_text, entity_info = annotation
    raw_text = raw_text.strip()
    
    entities = entity_info['entities']
    tokens = tokenize_raw_text(raw_text)
    tags = ['O'] * len(tokens) # Default all tags to 'O'

    # --- 2. Map Character Spans to Tokens ---
    token_spans = []
    current_char_index = 0
    for token in tokens:
        start = raw_text.find(token, current_char_index)
        if start == -1:
            continue
        end = start + len(token)
        token_spans.append((token, start, end))
        current_char_index = end

    # --- 3. Assign BIOES Tags based on Spans ---
    # This section is modified for BIOES tagging
    for ent_start, ent_end, ent_label in entities:
        # Find all token indices that fall within the current entity span
        entity_token_indices = []
        for i, (token, token_start, token_end) in enumerate(token_spans):
            # Check for full containment
            if token_start >= ent_start and token_end <= ent_end:
                entity_token_indices.append(i)

        # Apply BIOES tags based on the number of tokens in the entity
        if len(entity_token_indices) == 1:
            # Single-token entity
            idx = entity_token_indices[0]
            tags[idx] = f'S-{ent_label}'
        elif len(entity_token_indices) > 1:
            # Multi-token entity
            start_idx = entity_token_indices[0]
            end_idx = entity_token_indices[-1]
            tags[start_idx] = f'B-{ent_label}'
            tags[end_idx] = f'E-{ent_label}'
            # Tag tokens in the middle as 'I'
            for i in range(1, len(entity_token_indices) - 1):
                mid_idx = entity_token_indices[i]
                tags[mid_idx] = f'I-{ent_label}'
    
    # --- 4. Enforce Punctuation Rule ---
    for i, token in enumerate(tokens):
        if token in ['.', ',', ':', '!']:
            tags[i] = 'O'

    # --- 5. Format the Final CoNLL Output ---
    conll_output = [f"{token} {tag}" for token, tag in zip(tokens, tags)]
    return "\n".join(conll_output)

def process_spacy_data(data: List[List[Union[str, Dict[str, Any]]]]) -> str:
    """
    Processes a list of SpaCy annotations and converts them to a single
    CoNLL formatted string, with each annotation separated by a blank line.

    Args:
        data: A list of SpaCy annotation items.

    Returns:
        A single string with all annotations in CoNLL format.
    """
    all_conll_outputs = []
    for annotation in data:
        all_conll_outputs.append(spacy_to_conll(annotation))
    
    # Join each processed annotation with a double newline for CoNLL sentence separation
    return "\n\n".join(all_conll_outputs)


def save_to_excel(conll_string: str, output_path: str):
    """
    Parses a CoNLL formatted string and saves it to an Excel file
    with columns: sentence_id, word, tag.

    Args:
        conll_string: The CoNLL data as a single string.
        output_path: The path to save the .xlsx file (e.g., "annotations.xlsx").
    """
    print(f"Preparing data for Excel export...")
    
    # Split the string into blocks for each sentence/annotation
    sentences = conll_string.strip().split('\n\n')
    
    records = []
    # Enumerate sentences to get a sentence_id
    for sentence_id, sentence_block in enumerate(sentences, 1):
        lines = sentence_block.split('\n')
        for line in lines:
            if not line:
                continue
            # Split the line into word and tag
            word, tag = line.split()
            records.append({
                'sentence_id': sentence_id,
                'word': word,
                'tag': tag
            })
    
    # Create a pandas DataFrame from the list of records
    df = pd.DataFrame(records)
    
    # Save the DataFrame to an Excel file
    # index=False prevents pandas from writing row numbers into the file
    df.to_excel(output_path, index=False)
    
    print(f"Successfully saved annotations to {output_path}")


# --- Example Usage ---
if __name__ == "__main__":
    with open('annotations.json', 'r', encoding="utf-8") as file:
        data = json.load(file)
    annotations = data['annotations']
    # 1. Process the raw data into CoNLL format
    final_conll_dataset = process_spacy_data(annotations)

    # 2. Save the CoNLL data to an Excel file
    excel_filename = "annotations.xlsx"
    save_to_excel(final_conll_dataset, excel_filename)