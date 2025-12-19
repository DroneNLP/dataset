import pandas as pd
import re
from typing import List, Tuple, Dict

def validate_bioes_tags(input_csv_path: str, validation_output_path: str):
    """
    Validate BIOES tagging scheme and create a comprehensive validation file with ALL tokens.
    
    Args:
        input_csv_path: Path to input CSV with columns: sentence_id, word, tag
        validation_output_path: Path to output CSV with ALL tokens and validation info
    """
    
    # Read the input CSV
    df = pd.read_excel(input_csv_path)
    
    # Ensure required columns exist
    required_columns = ['sentence_id', 'word', 'tag']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"Input CSV must contain columns: {required_columns}")
    
    # Initialize list to store ALL validation results
    all_validation_results = []
    
    # Group by sentence_id to validate each sentence separately
    for sentence_id, group in df.groupby('sentence_id'):
        tokens = group['word'].tolist()
        tags = group['tag'].tolist()
        
        # Validate the tag sequence for this sentence (includes ALL tokens)
        sentence_results = validate_sentence_tags_comprehensive(sentence_id, tokens, tags)
        all_validation_results.extend(sentence_results)
    
    # Create DataFrame with ALL tokens
    validation_df = pd.DataFrame(all_validation_results)
    validation_df.to_excel(validation_output_path, index=False)
    
    # Count invalid tokens for summary
    invalid_count = len(validation_df[validation_df['status'] == 'invalid'])
    total_count = len(validation_df)
    
    print(f"Validation complete:")
    print(f"  Total tokens: {total_count}")
    print(f"  Invalid tokens: {invalid_count}")
    print(f"  Valid tokens: {total_count - invalid_count}")
    print(f"Results saved to: {validation_output_path}")
    
    return all_validation_results

def validate_sentence_tags_comprehensive(sentence_id: int, tokens: List[str], tags: List[str]) -> List[Dict]:
    """
    Validate BIOES tags for a single sentence and return ALL tokens with their validation status.
    """
    
    results = []
    
    for i, (token, tag) in enumerate(zip(tokens, tags)):
        status = "valid"
        information = ""
        
        # Parse the tag
        if tag == 'O':
            tag_prefix = 'O'
            entity_type = None
        else:
            # Check if tag follows BIOES-ENTITY format
            tag_parts = tag.split('-', 1)
            if len(tag_parts) != 2:
                status = "invalid"
                information = f"Tag '{tag}' does not follow BIOES-ENTITY format"
            else:
                tag_prefix, entity_type = tag_parts
                
                # Check if prefix is valid BIOES
                if tag_prefix not in ['B', 'I', 'O', 'E', 'S']:
                    status = "invalid"
                    information = f"Invalid tag prefix '{tag_prefix}'. Must be one of: B, I, O, E, S"
        
        # If basic format is valid, check sequence rules
        if status == "valid":
            validation_error = check_bioes_sequence_rules(tags, i, tag_prefix, entity_type if tag != 'O' else None)
            if validation_error:
                status = "invalid"
                information = validation_error
        
        # Add result for ALL tokens (valid and invalid)
        results.append({
            'sentence_id': sentence_id,
            'token_idx': i,
            'word': token,
            'tag': tag,
            'status': status,
            'information': information if information else "Valid according to BIOES rules"
        })
    
    return results

def check_bioes_sequence_rules(tags: List[str], current_idx: int, tag_prefix: str, entity_type: str) -> str:
    """
    Check BIOES sequence rules for a specific token position.
    Returns error message if invalid, empty string if valid.
    """
    
    def parse_tag(tag):
        if tag == 'O':
            return 'O', None
        parts = tag.split('-', 1)
        return parts[0] if len(parts) >= 1 else '', parts[1] if len(parts) == 2 else None
    
    prev_tag = tags[current_idx - 1] if current_idx > 0 else None
    next_tag = tags[current_idx + 1] if current_idx < len(tags) - 1 else None
    
    prev_prefix, prev_entity = parse_tag(prev_tag) if prev_tag else (None, None)
    next_prefix, next_entity = parse_tag(next_tag) if next_tag else (None, None)
    
    # Rule checks based on current tag prefix
    if tag_prefix == 'B':
        # B- must be followed by I- or E- of the same entity type
        if next_tag is None:
            return "B- tag at end of sentence must be followed by I- or E- of the same entity type"
        if next_prefix not in ['I', 'E']:
            return f"B- tag must be followed by I- or E-, found '{next_prefix}-' instead"
        if next_entity != entity_type:
            return f"B-{entity_type} must be followed by I-{entity_type} or E-{entity_type}, found {next_tag}"
    
    elif tag_prefix == 'I':
        # I- must be preceded by B- or I- of the same entity type
        if prev_tag is None:
            return "I- tag cannot be at the beginning of sentence"
        if prev_prefix not in ['B', 'I']:
            return f"I- tag must be preceded by B- or I-, found '{prev_prefix}-' instead"
        if prev_entity != entity_type:
            return f"I-{entity_type} must be preceded by B-{entity_type} or I-{entity_type}, found {prev_tag}"
        
        # I- must be followed by I- or E- of the same entity type (if not at end)
        if next_tag is not None:
            if next_prefix not in ['I', 'E', 'O', 'B', 'S']:  # Can be followed by anything, but if I/E must match entity
                return f"I- tag followed by invalid tag prefix '{next_prefix}'"
            if next_prefix in ['I', 'E'] and next_entity != entity_type:
                return f"I-{entity_type} followed by {next_tag}, entity types must match"
    
    elif tag_prefix == 'E':
        # E- must be preceded by B- or I- of the same entity type
        if prev_tag is None:
            return "E- tag cannot be at the beginning of sentence"
        if prev_prefix not in ['B', 'I']:
            return f"E- tag must be preceded by B- or I-, found '{prev_prefix}-' instead"
        if prev_entity != entity_type:
            return f"E-{entity_type} must be preceded by B-{entity_type} or I-{entity_type}, found {prev_tag}"
    
    elif tag_prefix == 'S':
        # S- represents a complete single-token entity, no specific sequence requirements
        # But it shouldn't be part of a multi-token entity
        if prev_tag and prev_prefix in ['B', 'I']:
            return f"S- tag cannot follow B- or I- tag (found after {prev_tag})"
        if next_tag and next_prefix in ['I', 'E']:
            return f"S- tag cannot be followed by I- or E- tag (followed by {next_tag})"
    
    # tag_prefix == 'O' has no sequence requirements
    
    return ""  # No error found

def apply_corrections(original_csv_path: str, correction_excel_path: str, output_csv_path: str):
    """
    Apply corrections from an Excel correction log to the original annotations.
    
    Args:
        original_csv_path: Path to original CSV with annotations
        correction_excel_path: Path to Excel file with corrections (columns: sentence_id, token_idx, corrected_tag)
        output_csv_path: Path to save corrected annotations
    """
    
    # Read original data
    original_df = pd.read_excel(original_csv_path)
    
    try:
        # Read correction log from Excel
        corrections_df = pd.read_excel(correction_excel_path)
        
        # Ensure required columns exist in corrections
        required_correction_columns = ['sentence_id', 'token_idx', 'corrected_tag']
        if not all(col in corrections_df.columns for col in required_correction_columns):
            raise ValueError(f"Correction Excel must contain columns: {required_correction_columns}")
        
        # Remove any rows with empty corrected_tag (in case user left some blank)
        corrections_df = corrections_df.dropna(subset=['corrected_tag'])
        
        print(f"Loaded {len(corrections_df)} corrections from {correction_excel_path}")
        
        # Create a copy of original data for corrections
        corrected_df = original_df.copy()
        
        # Apply corrections
        corrections_applied = 0
        for _, correction in corrections_df.iterrows():
            sentence_id = correction['sentence_id']
            token_idx = correction['token_idx']
            new_tag = correction['corrected_tag']
            
            # Find the matching row in original data
            mask = (corrected_df['sentence_id'] == sentence_id)
            sentence_data = corrected_df[mask].reset_index(drop=True)
            
            if token_idx < len(sentence_data):
                # Find the actual index in the full dataframe
                actual_idx = corrected_df[mask].index[token_idx]
                old_tag = corrected_df.loc[actual_idx, 'tag']
                corrected_df.loc[actual_idx, 'tag'] = new_tag
                corrections_applied += 1
                print(f"  Sentence {sentence_id}, Token {token_idx}: '{old_tag}' -> '{new_tag}'")
            else:
                print(f"  Warning: Token index {token_idx} not found in sentence {sentence_id}")
        
        # Save corrected data
        corrected_df.to_excel(output_csv_path, index=False)
        
        print(f"\nCorrections applied: {corrections_applied}")
        print(f"Corrected annotations saved to: {output_csv_path}")
        
        return corrected_df
        
    except FileNotFoundError:
        print(f"Error: Correction file '{correction_excel_path}' not found.")
        return None
    except Exception as e:
        print(f"Error applying corrections: {str(e)}")
        return None

def create_correction_template(validation_csv_path: str, template_excel_path: str):
    """
    Create an Excel template for corrections based on invalid tokens.
    
    Args:
        validation_csv_path: Path to validation CSV file
        template_excel_path: Path to save Excel template
    """
    
    # Read validation results
    validation_df = pd.read_excel(validation_csv_path)
    
    # Filter only invalid tokens
    invalid_tokens = validation_df[validation_df['status'] == 'invalid'].copy()
    
    if len(invalid_tokens) == 0:
        print("No invalid tokens found. No correction template needed.")
        return
    
    # Create correction template with additional column
    correction_template = invalid_tokens[['sentence_id', 'token_idx', 'word', 'tag', 'information']].copy()
    correction_template['corrected_tag'] = correction_template['tag']  # Pre-fill with current tag for easy editing
    
    # Save to Excel for easy editing
    correction_template.to_excel(template_excel_path, index=False)
    
    print(f"Correction template created: {template_excel_path}")
    print(f"Template contains {len(correction_template)} invalid tokens to correct.")
    print("Edit the 'corrected_tag' column with the correct tags, then use apply_corrections() function.")

def main():
    """
    Example usage of the BIOES validation and correction system.
    """
    # File paths - modify these according to your needs
    input_file = "spacy_to_conll.xlsx"           # Your original annotations
    validation_file = "validation_results.xlsx"     # All tokens with validation info
    correction_template = "correction_template.xlsx"  # Template for making corrections
    correction_log = "correction_log.xlsx"         # Your completed corrections
    corrected_output = "corrected-step-1.csv"     # Final corrected annotations
    
    print("=== BIOES Validation and Correction System ===\n")
    
    try:
        # Step 1: Validate annotations and create comprehensive validation file
        print("Step 1: Validating BIOES tags...")
        validation_results = validate_bioes_tags(input_file, validation_file)
        
        # Step 2: Create correction template (only if there are invalid tokens)
        print(f"\nStep 2: Creating correction template...")
        create_correction_template(validation_file, correction_template)
        
        # Step 3: Apply corrections (only run this after you've created your correction log)
        print(f"\nStep 3: To apply corrections later, use:")
        print(f"apply_corrections('{input_file}', '{correction_log}', '{corrected_output}')")
        
        # Uncomment the line below when you have your correction_log.xlsx ready:
        # apply_corrections(input_file, correction_log, corrected_output)
        
    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        print("Make sure your input file exists and the path is correct.")
    except Exception as e:
        print(f"Error during processing: {str(e)}")

if __name__ == "__main__":
    main()