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
                        'tag': original_tag,
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
                        'tag': structure_tag,
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
    Fix BIOES sequence structure violations using ordered heuristic rules.
    
    IMPORTANT: Use O tag as span separator. One span is preceded and ended by O tag.
    
    Ordered Heuristics:
    1. For isolated B/I/E tags after O and followed by O tag -> change to S-tag
    2. Missing B- at start of entity (O followed by I/E tag) -> convert first to B-
    3. Multiple E- tags before O -> convert all but last to I-
    4. Incomplete entities -> complete with E-
    """
    
    if not tags:
        return tags
    
    def parse_tag(tag):
        if tag == 'O':
            return 'O', None
        parts = tag.split('-', 1)
        return parts[0] if len(parts) >= 1 else 'O', parts[1] if len(parts) == 2 else None
    
    corrected = tags.copy()
    
    # Rule 1: For isolated B/I/E tags after O and followed by O tag -> change to S-tag
    for i in range(len(corrected)):
        current_prefix, current_entity = parse_tag(corrected[i])
        
        if current_prefix in ['B', 'I', 'E']:
            # Check if this tag is isolated (O before and O after)
            prev_is_o = (i == 0) or (parse_tag(corrected[i - 1])[0] == 'O')
            next_is_o = (i == len(corrected) - 1) or (parse_tag(corrected[i + 1])[0] == 'O')
            
            if prev_is_o and next_is_o:
                # Isolated tag -> convert to S-
                corrected[i] = f'S-{current_entity}'
    
    # Rule 2: Missing B- at start of entity (O followed by I/E tag) -> convert first to B-
    for i in range(len(corrected)):
        current_prefix, current_entity = parse_tag(corrected[i])
        
        if current_prefix in ['I', 'E']:
            # Check if preceded by O (or start of sentence)
            prev_is_o = (i == 0) or (parse_tag(corrected[i - 1])[0] == 'O')
            
            if prev_is_o:
                # Missing B- at start -> convert to B-
                corrected[i] = f'B-{current_entity}'
    
    # Rule 3: Multiple E- tags before O -> convert all but last to I-
    i = 0
    while i < len(corrected):
        current_prefix, current_entity = parse_tag(corrected[i])
        
        if current_prefix == 'E':
            # Find all consecutive E- tags of the same entity before O or end
            consecutive_e_positions = [i]
            j = i + 1
            
            while j < len(corrected):
                next_prefix, next_entity = parse_tag(corrected[j])
                if next_prefix == 'E' and next_entity == current_entity:
                    consecutive_e_positions.append(j)
                    j += 1
                else:
                    break
            
            # Convert all E- tags except the last one to I-
            if len(consecutive_e_positions) > 1:
                for pos in consecutive_e_positions[:-1]:  # All except last
                    _, entity = parse_tag(corrected[pos])
                    corrected[pos] = f'I-{entity}'
            
            i = j
        else:
            i += 1
    
    # Rule 4: Incomplete entities -> complete with E-
    for i in range(len(corrected)):
        current_prefix, current_entity = parse_tag(corrected[i])
        
        if current_prefix in ['B', 'I']:
            # Check what follows this tag
            if i == len(corrected) - 1:
                # At end of sentence
                if current_prefix == 'B':
                    # Lone B- at end -> convert to S-
                    corrected[i] = f'S-{current_entity}'
                elif current_prefix == 'I':
                    # I- at end -> convert to E-
                    corrected[i] = f'E-{current_entity}'
            else:
                next_prefix, next_entity = parse_tag(corrected[i + 1])
                
                if next_prefix == 'O':
                    # Entity span ends at O
                    if current_prefix == 'B':
                        # B- followed by O -> convert to S-
                        corrected[i] = f'S-{current_entity}'
                    elif current_prefix == 'I':
                        # I- followed by O -> convert to E-
                        corrected[i] = f'E-{current_entity}'
                elif next_prefix in ['B', 'S'] or (next_prefix in ['I', 'E'] and next_entity != current_entity):
                    # Entity span ends before different entity
                    if current_prefix == 'B':
                        # B- followed by different entity -> convert to S-
                        corrected[i] = f'S-{current_entity}'
                    elif current_prefix == 'I':
                        # I- followed by different entity -> convert to E-
                        corrected[i] = f'E-{current_entity}'
    
    return corrected

def fix_entity_type_consistency(tags: List[str]) -> List[str]:
    """
    Fix entity type consistency within BIOES spans.
    
    Strategy: 
    1. For each span, use majority vote of entity types
    2. In case of tie (even number of tokens with equal conflicting types), 
       use the first token's (B-tag) entity type
    3. Only apply this after BIOES structure is valid
    """
    
    if not tags:
        return tags
    
    def parse_tag(tag):
        if tag == 'O':
            return 'O', None
        parts = tag.split('-', 1)
        return parts[0] if len(parts) >= 1 else 'O', parts[1] if len(parts) == 2 else None
    
    corrected = tags.copy()
    i = 0
    
    while i < len(corrected):
        current_prefix, current_entity = parse_tag(corrected[i])
        
        if current_prefix == 'B':
            # Found start of entity span - find the complete span
            span_start = i
            span_end = i
            span_positions = [i]
            entity_types = [current_entity] if current_entity else []
            first_token_entity = current_entity  # Remember B-tag's entity type
            
            # Look for the end of the span
            j = i + 1
            while j < len(corrected):
                next_prefix, next_entity = parse_tag(corrected[j])
                
                if next_prefix == 'I':
                    entity_types.append(next_entity)
                    span_positions.append(j)
                    span_end = j
                elif next_prefix == 'E':
                    entity_types.append(next_entity)
                    span_positions.append(j)
                    span_end = j
                    break  # End of span found
                else:
                    # Span ends (shouldn't happen if BIOES structure is fixed)
                    break
                j += 1
            
            # Determine the correct entity type for this span
            if len(set(entity_types)) > 1:
                # Multiple entity types in span - need correction
                entity_counter = Counter(entity_types)
                most_common_counts = entity_counter.most_common()
                
                # Check if there's a clear majority
                if len(most_common_counts) > 1 and most_common_counts[0][1] == most_common_counts[1][1]:
                    # Tie situation - use first token's (B-tag) entity type
                    correct_entity = first_token_entity
                    print(f"  Tie-breaking: Using first token's entity type '{correct_entity}' for span at positions {span_positions}")
                else:
                    # Clear majority
                    correct_entity = most_common_counts[0][0]
                
                # Apply correction to the entire span
                for pos in span_positions:
                    tag_prefix, _ = parse_tag(corrected[pos])
                    corrected[pos] = f'{tag_prefix}-{correct_entity}'
            
            i = span_end + 1
            
        elif current_prefix == 'S':
            # Single token entity - no consistency issues within span
            i += 1
        else:
            # O or other tags
            i += 1
    
    return corrected

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
            print(group)
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
    Example usage of the heuristic correction system.
    """
    input_file = "airdata-prediction.xlsx"
    corrected_file = "heuristic_corrected.xlsx"
    
    print("=== NER Heuristic Correction System ===\n")
    
    # Apply heuristic corrections
    corrected_df, corrections = apply_heuristic_corrections(input_file, corrected_file)
    
    # Evaluate improvements
    evaluate_before_after_correction(input_file, corrected_file)
    
    print(f"\nRecommendation:")
    print(f"1. Report both raw model performance (using {input_file})")
    print(f"2. Report post-processed performance (using {corrected_file})")
    print(f"3. This provides a complete picture of your model's capabilities")

if __name__ == "__main__":
    main()