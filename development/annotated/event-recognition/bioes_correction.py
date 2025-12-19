import pandas as pd
from typing import List, Tuple, Dict
from collections import Counter

def apply_heuristic_corrections(input_csv_path: str, output_csv_path: str, log_corrections: bool = True):
    """
    Apply heuristic corrections to fix BIOES sequence violations and entity type inconsistencies.
    
    Two-stage process:
    1. Fix BIOES structure violations first (ensure valid sequences)
    2. Fix entity type consistency within valid spans
    
    Args:
        input_csv_path: Path to input CSV with columns: sentence_id, word, tag
        output_csv_path: Path to save corrected annotations
        log_corrections: Whether to log corrections made
    """
    
    # Read the input CSV
    df = pd.read_excel(input_csv_path)
    
    # Ensure required columns exist
    required_columns = ['sentence_id', 'word', 'tag']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"Input CSV must contain columns: {required_columns}")
    
    corrected_df = df.copy()
    structure_corrections = []
    type_corrections = []
    
    print("=== Stage 1: Fixing BIOES Structure Violations ===")
    
    # Stage 1: Process each sentence for structure corrections
    for sentence_id, group in df.groupby('sentence_id'):
        original_tags = group['tag'].tolist()
        
        # Step 1: Fix BIOES sequence structure
        structure_corrected_tags = fix_bioes_structure(original_tags)
        
        # Update the dataframe and log structure corrections
        sentence_indices = group.index
        for i, (original_tag, corrected_tag) in enumerate(zip(original_tags, structure_corrected_tags)):
            if original_tag != corrected_tag:
                corrected_df.loc[sentence_indices[i], 'tag'] = corrected_tag
                if log_corrections:
                    structure_corrections.append({
                        'sentence_id': sentence_id,
                        'token_idx': i,
                        'word': group.iloc[i]['word'],
                        'original_tag': original_tag,
                        'corrected_tag': corrected_tag,
                        'correction_type': 'structure_correction'
                    })
    
    print(f"Structure corrections applied: {len(structure_corrections)}")
    
    print("\n=== Stage 2: Fixing Entity Type Consistency ===")
    
    # Stage 2: Process each sentence for entity type consistency
    # (using the structure-corrected tags from Stage 1)
    for sentence_id, group in corrected_df.groupby('sentence_id'):
        structure_corrected_tags = group['tag'].tolist()
        
        # Step 2: Fix entity type consistency within spans
        final_tags = fix_entity_type_consistency(structure_corrected_tags)
        
        # Update the dataframe and log type corrections
        sentence_indices = group.index
        for i, (structure_tag, final_tag) in enumerate(zip(structure_corrected_tags, final_tags)):
            if structure_tag != final_tag:
                corrected_df.loc[sentence_indices[i], 'tag'] = final_tag
                if log_corrections:
                    type_corrections.append({
                        'sentence_id': sentence_id,
                        'token_idx': i,
                        'word': group.iloc[i]['word'],
                        'original_tag': structure_tag,
                        'corrected_tag': final_tag,
                        'correction_type': 'entity_type_correction'
                    })
    
    print(f"Entity type corrections applied: {len(type_corrections)}")
    
    # Save corrected annotations
    corrected_df.to_excel(output_csv_path, index=False)
    
    # Combine all corrections for logging
    all_corrections = structure_corrections + type_corrections
    total_corrections = len(all_corrections)
    
    print(f"\n=== Summary ===")
    print(f"Total corrections applied: {total_corrections}")
    print(f"  - BIOES structure corrections: {len(structure_corrections)}")
    print(f"  - Entity type corrections: {len(type_corrections)}")
    
    # Save detailed correction log if requested
    if log_corrections and total_corrections > 0:
        correction_log_df = pd.DataFrame(all_corrections)
        log_path = output_csv_path.replace('.xlsx', '_correction_log.xlsx')
        correction_log_df.to_excel(log_path, index=False)
        print(f"Detailed correction log saved to: {log_path}")
    
    return corrected_df, all_corrections

def fix_bioes_structure(tags: List[str]) -> List[str]:
    """
    Fix BIOES sequence structure violations using span-based approach.
    
    IMPORTANT: O tags are correct and serve as span separators.
    Task: Fix everything between O tags to follow BIOES rules.
    
    Algorithm:
    1. Identify all spans between O tags
    2. For each span:
       - If 1 token: convert to S-TYPE
       - If multiple tokens: B-TYPE I-TYPE* E-TYPE (same TYPE)
    """
    
    if not tags:
        return tags
    
    def parse_tag(tag):
        if tag == 'O':
            return 'O', None
        parts = tag.split('-', 1)
        return parts[0] if len(parts) >= 1 else 'O', parts[1] if len(parts) == 2 else None
    
    corrected = tags.copy()
    
    # Find all spans between O tags
    i = 0
    while i < len(corrected):
        if parse_tag(corrected[i])[0] == 'O':
            i += 1
            continue
        
        # Found start of a span (non-O tag)
        span_start = i
        span_end = i
        
        # Find end of span (next O tag or end of sequence)
        while span_end + 1 < len(corrected) and parse_tag(corrected[span_end + 1])[0] != 'O':
            span_end += 1
        
        # Now we have a span from span_start to span_end (inclusive)
        span_length = span_end - span_start + 1
        
        if span_length == 1:
            # Single token span -> must be S-TYPE
            _, entity_type = parse_tag(corrected[span_start])
            corrected[span_start] = f'S-{entity_type}'
        
        else:
            # Multi-token span -> must be B-TYPE I-TYPE* E-TYPE
            # First, determine the entity type for the entire span
            span_tags = corrected[span_start:span_end+1]
            entity_type = determine_span_entity_type(span_tags)
            
            # Apply correct BIOES structure
            corrected[span_start] = f'B-{entity_type}'  # First token
            for j in range(span_start + 1, span_end):   # Middle tokens
                corrected[j] = f'I-{entity_type}'
            corrected[span_end] = f'E-{entity_type}'    # Last token
        
        # Move to next position after this span
        i = span_end + 1
    
    return corrected

def determine_span_entity_type(span_tags: List[str]) -> str:
    """
    Determine the correct entity type for a span.
    
    Strategy:
    1. Use majority vote of entity types in the span
    2. In case of tie, use the first token's entity type
    """
    
    def parse_tag(tag):
        if tag == 'O':
            return 'O', None
        parts = tag.split('-', 1)
        return parts[0] if len(parts) >= 1 else 'O', parts[1] if len(parts) == 2 else None
    
    entity_types = []
    first_token_type = None
    
    for i, tag in enumerate(span_tags):
        _, entity_type = parse_tag(tag)
        if entity_type:
            entity_types.append(entity_type)
            if i == 0:  # First token
                first_token_type = entity_type
    
    if not entity_types:
        return "UNKNOWN"  # Fallback, shouldn't happen
    
    # Count entity types
    entity_counter = Counter(entity_types)
    most_common = entity_counter.most_common()
    
    # Check for tie
    if len(most_common) > 1 and most_common[0][1] == most_common[1][1]:
        # Tie case - use first token's entity type
        return first_token_type
    else:
        # Clear majority
        return most_common[0][0]

def fix_entity_type_consistency(tags: List[str]) -> List[str]:
    """
    Fix entity type consistency within BIOES spans.
    This function should only be called AFTER fix_bioes_structure() 
    has ensured all spans follow correct BIOES structure.
    
    At this point, all spans are either:
    - O S-TYPE O (single token)
    - O B-TYPE I-TYPE* E-TYPE O (multi-token)
    
    Task: Ensure all tokens in each span have the same entity type.
    """
    
    # Since structure is already fixed, this function is now redundant
    # The structure fixing already handles entity type consistency
    # by calling determine_span_entity_type() for each span
    
    return tags

def evaluate_before_after_correction(original_csv: str, corrected_csv: str, gold_csv: str = None):
    """
    Evaluate model performance before and after heuristic corrections.
    
    Args:
        original_csv: Path to original predictions
        corrected_csv: Path to corrected predictions
        gold_csv: Path to gold standard (optional, for actual evaluation)
    """
    
    original_df = pd.read_excel(original_csv)
    corrected_df = pd.read_excel(corrected_csv)
    
    print("=== Evaluation: Before vs After Heuristic Corrections ===")
    
    # Basic statistics
    print("\n1. BIOES Structure Compliance:")
    
    def count_structure_violations(df):
        violations = 0
        for sentence_id, group in df.groupby('sentence_id'):
            tags = group['tag'].tolist()
            for i, tag in enumerate(tags):
                if is_structure_violation(tags, i):
                    violations += 1
        return violations
    
    original_violations = count_structure_violations(original_df)
    corrected_violations = count_structure_violations(corrected_df)
    
    print(f"  Original violations: {original_violations}")
    print(f"  After correction: {corrected_violations}")
    print(f"  Reduction: {original_violations - corrected_violations}")
    
    # Entity type consistency
    print("\n2. Entity Type Consistency:")
    original_inconsistent = count_type_inconsistencies(original_df)
    corrected_inconsistent = count_type_inconsistencies(corrected_df)
    
    print(f"  Original inconsistent spans: {original_inconsistent}")
    print(f"  After correction: {corrected_inconsistent}")
    print(f"  Reduction: {original_inconsistent - corrected_inconsistent}")
    
    if gold_csv:
        print("\n3. Performance vs Gold Standard:")
        # Here you would implement actual F1 evaluation
        print("  (Implement F1 evaluation against gold standard)")

def is_structure_violation(tags: List[str], pos: int) -> bool:
    """Check if a tag at given position violates BIOES structure."""
    # Simplified version - implement full validation logic here
    return False  # Placeholder

def count_type_inconsistencies(df: pd.DataFrame) -> int:
    """Count entity spans with inconsistent entity types."""
    inconsistencies = 0
    
    for sentence_id, group in df.groupby('sentence_id'):
        tags = group['tag'].tolist()
        
        def parse_tag(tag):
            if tag == 'O':
                return 'O', None
            parts = tag.split('-', 1)
            return parts[0] if len(parts) >= 1 else 'O', parts[1] if len(parts) == 2 else None
        
        i = 0
        while i < len(tags):
            prefix, entity = parse_tag(tags[i])
            
            if prefix == 'B':
                # Find span
                span_entities = [entity]
                j = i + 1
                while j < len(tags):
                    next_prefix, next_entity = parse_tag(tags[j])
                    if next_prefix in ['I', 'E']:
                        span_entities.append(next_entity)
                        if next_prefix == 'E':
                            break
                    else:
                        break
                    j += 1
                
                # Check consistency
                if len(set(span_entities)) > 1:
                    inconsistencies += 1
                
                i = j + 1
            else:
                i += 1
    
    return inconsistencies

def main():
    """
    BIOES correction system focused solely on fixing tag violations.
    """
    input_file = "annotations.xlsx"
    corrected_file = "annotations-bioes-corrected.xlsx"
    
    print("=== BIOES Tag Correction System ===\n")
    
    try:
        # Apply BIOES corrections
        corrected_df, corrections = apply_heuristic_corrections(input_file, corrected_file)
        print(f"\nCorrections completed. Results saved to: {corrected_file}")
        
    except FileNotFoundError as e:
        print(f"Error: Input file not found - {input_file}")
    except Exception as e:
        print(f"Error during correction: {str(e)}")

if __name__ == "__main__":
    main()