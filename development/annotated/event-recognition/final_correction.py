import pandas as pd

def apply_corrections_from_log(
    main_annotations_path: str,
    correction_log_path: str,
    output_path: str
):
    """
    Updates tags in a main annotations file based on a correction log.

    The function aligns rows using 'sentence_id' and 'token_idx' and
    updates the 'tag' column in the main data with the corresponding
    tag from the correction log.

    Args:
        main_annotations_path: Path to the primary annotations Excel file.
        correction_log_path: Path to the Excel file containing tag corrections.
        output_path: Path to save the final, updated annotations Excel file.
    """
    print(f"Reading main annotations from '{main_annotations_path}'...")
    main_df = pd.read_excel(main_annotations_path)

    print(f"Reading correction log from '{correction_log_path}'...")
    log_df = pd.read_excel(correction_log_path)

    # --- Core Logic: Update based on matching indices ---
    
    # To efficiently update, we'll set a unique index on both DataFrames.
    # The combination of sentence_id and token_idx uniquely identifies each word.
    main_df.set_index(['sentence_id', 'token_idx'], inplace=True)
    log_df.set_index(['sentence_id', 'token_idx'], inplace=True)

    print(f"Applying {len(log_df)} corrections...")
    
    # The update() method modifies main_df in place.
    # For any index that exists in both DataFrames, it updates the columns
    # of main_df with the values from log_df.
    main_df.update(log_df)

    # After updating, we can restore the indices back to columns.
    main_df.reset_index(inplace=True)

    print(f"Saving final corrected annotations to '{output_path}'...")
    # Ensure the output columns are in the original order
    final_df = main_df[['sentence_id', 'word', 'tag', 'token_idx']]
    final_df.to_excel(output_path, index=False)
    
    print("Correction process complete.")


# --- Example Usage ---
if __name__ == '__main__':
    # Define the file paths
    main_file = 'annotations-parenthesis-corrected.xlsx'
    log_file = 'colon_correction_log.xlsx'
    output_file = 'annotations-colon-corrected.xlsx'

    # Run the main function to apply the corrections
    apply_corrections_from_log(
        main_annotations_path=main_file,
        correction_log_path=log_file,
        output_path=output_file
    )