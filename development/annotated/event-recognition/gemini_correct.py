import pandas as pd
from collections import Counter

def process_span(span_rows):
    """
    Corrects a single entity span for BIOES tagging and entity type consistency.

    Args:
        span_rows (list): A list of dictionaries, where each dictionary represents a row (token)
                          within the entity span.

    Returns:
        list: A list of corrected dictionaries for the span.
    """
    n = len(span_rows)
    if n == 0:
        return []

    # --- 1. Entity Type Correction (Majority Voting) ---
    # Extract entity types from the tags (e.g., 'PER' from 'B-PER')
    entity_types = [row['tag'].split('-', 1)[1] for row in span_rows if '-' in row['tag']]

    # If for some reason no valid entity types are found, return the original span
    if not entity_types:
        return span_rows

    # Count the occurrences of each entity type
    counts = Counter(entity_types)
    max_count = max(counts.values())
    
    # Find all types with the maximum count
    majority_candidates = [etype for etype, count in counts.items() if count == max_count]

    # Apply tie-breaking rule: if there's a tie, use the first token's entity type
    if len(majority_candidates) > 1:
        majority_type = entity_types[0]
    else:
        majority_type = majority_candidates[0]

    # --- 2. BIOES Tag Correction ---
    corrected_span = []
    if n == 1:
        # Rule 3: Single-word entity gets the 'S-' tag
        row = span_rows[0].copy()
        row['tag'] = f"S-{majority_type}"
        corrected_span.append(row)
    else:
        # Multi-word entity
        # Rule 4: Token after 'O' (the first in a span) should be 'B-'
        first_row = span_rows[0].copy()
        first_row['tag'] = f"B-{majority_type}"
        corrected_span.append(first_row)

        # Rule 6: All intermediary tokens are assigned 'I-'
        for i in range(1, n - 1):
            row = span_rows[i].copy()
            row['tag'] = f"I-{majority_type}"
            corrected_span.append(row)

        # Rule 5: Token before 'O' (the last in a span) should be 'E-'
        last_row = span_rows[-1].copy()
        last_row['tag'] = f"E-{majority_type}"
        corrected_span.append(last_row)

    return corrected_span

def correct_ner_tags(df):
    """
    Applies heuristic corrections to NER tags in a DataFrame.

    Args:
        df (pd.DataFrame): DataFrame with 'sentence_id', 'word', and 'tag' columns.

    Returns:
        pd.DataFrame: A new DataFrame with the corrected tags.
    """
    corrected_data = []
    # Group by sentence_id to process each sentence independently
    for _, group in df.groupby('sentence_id'):
        sentence_rows = [row for _, row in group.iterrows()]
        current_span = []

        for row in sentence_rows:
            # Rule 1: 'O' tag acts as a span separator
            if row['tag'] == 'O':
                # If a span was being built, it has now ended. Process it.
                if current_span:
                    processed_span = process_span(current_span)
                    corrected_data.extend(processed_span)
                    current_span = []  # Reset for the next span
                
                # Add the 'O' tag row itself to our results
                corrected_data.append(row.to_dict())
            else:
                # This token is part of an entity, add it to the current span
                current_span.append(row)

        # After iterating through the sentence, process any remaining span
        # (This handles cases where a sentence ends with an entity)
        if current_span:
            processed_span = process_span(current_span)
            corrected_data.extend(processed_span)

    # Create a new DataFrame from the list of corrected row dictionaries
    if not corrected_data:
        return pd.DataFrame(columns=df.columns)
        
    corrected_df = pd.DataFrame(corrected_data)
    # Ensure the column order is the same as the input
    corrected_df = corrected_df[df.columns]
    return corrected_df

def create_sample_input_file(filename="input.xlsx"):
    """Creates a sample Excel file for demonstration."""
    data = {
        'sentence_id': [1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3],
        'word': [
            'Elon', 'Musk', 'founded', 'SpaceX', '.',
            'The', 'United', 'Nations', 'is', 'in', 'NY',
            'Apple', 'Inc.', 'is', 'a'
        ],
        'tag': [
            'B-PER', 'E-PER',      # Correct BIOES
            'O',
            'B-ORG',              # Single token, should be S-ORG
            'O',
            'O',
            'B-ORG', 'I-ORG',      # Correct BIOES
            'O',
            'O',
            'B-LOC',              # Single token, should be S-LOC
            'B-ORG', 'I-PERSON',   # Inconsistent entity type (tie)
            'O',
            'B-MISC'              # Entity at end of sentence
        ]
    }
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"Sample file '{filename}' created successfully.")

if __name__ == "__main__":
    # --- Setup ---
    input_filename = 'airdata-prediction.xlsx'
    output_filename = 'airdata-prediction-corrected.xlsx'
    
    # Create a sample file to run the script on
    # create_sample_input_file(input_filename)

    # --- Main Logic ---
    # try:
    # Load the data from the Excel file
    print(f"\nReading data from '{input_filename}'...")
    input_df = pd.read_excel(input_filename)
    print("Original Data:")
    print(input_df)

    # Apply the heuristic corrections
    print("\nApplying heuristic corrections...")
    corrected_df = correct_ner_tags(input_df)

    # Save the corrected data to a new Excel file
    corrected_df.to_excel(output_filename, index=False)
    print(f"\nCorrections complete. Results saved to '{output_filename}'.")
    print("Corrected Data:")
    print(corrected_df)

    # except FileNotFoundError:
    #     print(f"Error: The file '{input_filename}' was not found.")
    # except Exception as e:
    #     print(f"An unexpected error occurred: {e}")