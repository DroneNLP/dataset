import pandas as pd
from typing import List

def correct_sentence_tags(sentence_df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies correction logic for parenthesis-related tagging errors within a single sentence.
    
    Args:
        sentence_df: A DataFrame containing the data for one sentence_id.
        
    Returns:
        A DataFrame with corrected tags.
    """
    words = sentence_df['word'].tolist()
    tags = sentence_df['tag'].tolist()
    
    # --- Fix Case 2 First: Create new CONTEXT entities for O-tagged parenthetical blocks ---
    # Example: (Code : 180059)
    i = 0
    while i < len(words):
        # Look for the start of a potential block
        if words[i].startswith('(') and tags[i] == 'O':
            start_idx = i
            end_idx = -1
            
            # Look for the corresponding end
            for j in range(i, len(words)):
                if words[j].endswith(')'):
                    end_idx = j
                    break
            
            # If we found a start and an end
            if end_idx != -1:
                # Check if all tags in between are 'O'
                # is_all_O = all(tags[k] == 'O' for k in range(start_idx, end_idx + 1))
                
                # if is_all_O:
                    # Apply BIOES tagging to the block
                if start_idx == end_idx: # Single-token entity like "(Code)"
                    tags[start_idx] = 'S-CONTEXT'
                else: # Multi-token entity like "(Code : 180059)"
                    tags[start_idx] = 'B-CONTEXT'
                    tags[end_idx] = 'E-CONTEXT'
                    for k in range(start_idx + 1, end_idx):
                        tags[k] = 'I-CONTEXT'
                    
                # Skip the index to the end of the block we just tagged
                i = end_idx
        i += 1
        
    # --- Fix Case 1 Second: Extend existing entities to include adjacent parentheses ---
    # Example: Zone E-EVENT, (Airport O -> Zone I-EVENT, (Airport B-CONTEXT
    # Example: Power E-CONTEXT, Plant) O -> Power I-CONTEXT, Plant) E-CONTEXT
    for i in range(len(words)):
        # Extend to the right (absorb an opening parenthesis)
        if words[i].startswith('(') and tags[i] == 'O':
            if i + 1 < len(words) and tags[i+1].startswith('B-'):
                entity_type = tags[i+1][2:] # Get entity type like 'CONTEXT'
                tags[i] = f'B-{entity_type}'
                tags[i+1] = f'I-{entity_type}'

        # Extend to the left (absorb a closing parenthesis)
        if words[i].endswith(')') and tags[i] == 'O':
            if i > 0 and tags[i-1] != 'O':
                # Get entity type from the previous tag
                entity_type = tags[i-1][2:]
                tags[i] = f'E-{entity_type}'
                
                # Downgrade the previous tag if it was an S- or E-
                if tags[i-1].startswith('S-'):
                    tags[i-1] = f'B-{entity_type}'
                elif tags[i-1].startswith('E-'):
                    tags[i-1] = f'I-{entity_type}'

        if words[i].startswith('(') and words[i].endswith(')') and tags[i] == 'O':
            tags[i] = 'S-CONTEXT'

    sentence_df['tag'] = tags
    # Add token_idx (per sentence)
    sentence_df = sentence_df.reset_index(drop=True)
    sentence_df["token_idx"] = sentence_df.index
    return sentence_df

def fix_parenthesis_issues(input_excel_path: str, output_excel_path: str):
    """
    Reads an Excel file, corrects parenthesis-related tagging issues,
    and saves the result to a new Excel file.
    
    Args:
        input_excel_path: Path to the source Excel file.
        output_excel_path: Path to save the corrected Excel file.
    """
    print(f"Reading data from '{input_excel_path}'...")
    df = pd.read_excel(input_excel_path)
    
    print("Applying corrections for parenthesis edge cases...")
    # Group by sentence, apply the correction function, and combine the results
    corrected_df = df.groupby('sentence_id', group_keys=False).apply(correct_sentence_tags)
    
    print(f"Saving corrected data to '{output_excel_path}'...")
    corrected_df.to_excel(output_excel_path, index=False)
    print("Done.")

# --- How to Use ---
if __name__ == '__main__':
    # Define your input and output file names
    # Make sure 'your_annotations.xlsx' exists and is in the same directory
    # as this script, or provide the full path.
    input_file = 'annotations-bioes-corrected.xlsx' 
    output_file = 'annotations-parenthesis-corrected.xlsx'
    
    # Run the main correction function
    fix_parenthesis_issues(input_file, output_file)