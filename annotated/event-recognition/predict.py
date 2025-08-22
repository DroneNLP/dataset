import re
import os
import csv
import torch

import pandas as pd

from simpletransformers.ner import NERModel
from typing import List


def tokenize_raw_text(text: str) -> List[str]:
    """
    Tokenizes a single string into a list of tokens based on spaces
    and punctuation, correctly handling decimals, units, and complex units.
    
    Args:
        text: The input string to tokenize.
    
    Returns:
        A list of tokens.
    """
    # Strip whitespace
    text = text.strip()
    
    # Add period if doesn't end with punctuation
    if text and text[-1] not in '.!?,':
        text += '.'
    
    # Normalize spacing - single spaces between words
    text = re.sub(r'\s+', ' ', text)
    # This regex is updated to include '/' in the list of standalone punctuation.
    # tokens = re.findall(r"\d+(?:\.\d+)?(?:[a-zA-Z\/°]+)?|\d+(?:\.\d+)?|[\w']+|[.,!?;:()\[\]\/-]+", text)
    # tokens = re.findall(r"\d+(?:\.\d+)?(?:[a-zA-Z\/°]+)?|[\w']+|[.,!?;:()\[\]\/-]", text)
    # tokens = re.findall(r"\d+(?:\.\d+)?(?:[a-zA-Z\/°]+)?|[\w'()-]+|[.,!?;:]", text)
    # tokens = re.findall(r"\d+(?:\.\d+)?(?:[a-zA-Z\/°]+)?\)?|[\w'()-]+|[.,!?;:]", text)
    tokens = re.findall(r"[a-zA-Z0-9\/°'()_-]+|[.,!?;:]", text)

    return tokens

def tokenize_test_set(raw_messages: List[str]) -> List[List[str]]:
    """
    Tokenizes a list of raw messages (e.g., a test set).
    
    Args:
        raw_messages: A list of raw message strings.
        
    Returns:
        A list of lists of tokens.
    """
    tokenized_messages = []
    for message in raw_messages:
        tokenized_messages.append(tokenize_raw_text(message))
    return tokenized_messages


def export_predictions_to_conll(predictions_output, output_filepath):
    """
    Exports the predictions from simpletransformers' .predict() method
    to a CoNLL formatted file.

    The CoNLL format expects one token per line, followed by its entity tag,
    with an empty line separating sentences.

    Args:
        predictions_output (list): A list of lists of dictionaries,
                                   where each inner list represents a sentence
                                   and each dictionary contains 'token' and 'entity' keys.
                                   Example: [[{'token': 'Barack', 'entity': 'B-PER'},
                                              {'token': 'Obama', 'entity': 'I-PER'}],
                                             [{'token': 'lives', 'entity': 'O'},
                                              {'token': 'in', 'entity': 'O'},
                                              {'token': 'Washington', 'entity': 'B-LOC'},
                                              {'token': 'D.C.', 'entity': 'I-LOC'}]]
        output_filepath (str): The path to the file where the CoNLL output will be saved.
    """

    with open(output_filepath, 'w', encoding='utf-8') as f:
        for sentence_predictions in predictions_output:
            for pred_dict in sentence_predictions:
                for key, value in pred_dict.items():
                    f.write(f"{key} {value}\n")
            f.write("\n")  # Add an empty line after each sentence
    print(f"✅ Predictions successfully exported to: {os.path.abspath(output_filepath)}")
    # except Exception as e:
    #     print(f"❌ An error occurred while exporting predictions: {e}")

def conll_to_csv(source_file, dest_file):
    sentences = []
    tokens = []

    with open(source_file, "r") as file:
        for line in file:
            line = line.strip()
            if not line:  # empty line = sentence boundary
                if tokens:  # avoid appending empty sentences
                    sentences.append(tokens)
                    tokens = []
                continue
            
            word, tag = line.split()
            tokens.append((word, tag))

    # Append last sentence if not followed by an empty line
    if tokens:
        sentences.append(tokens)

    with open(dest_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["sentence_id", "word", "tag"])
        
        for sent_id, sentence in enumerate(sentences):
            for word, tag in sentence:
                writer.writerow([sent_id, word, tag])

def main():
    # --- Configuration ---
    # Replace 'your_username/your_model_repo' with your actual Hugging Face model repository ID.
    # Example: 'bert-base-cased-finetuned-ner'
    # You can also specify a local path if the model is downloaded.
    HUGGING_FACE_MODEL_PATH = os.path.join('annotated', 'event-recognition', 'ADFLER-xlnet-base-cased') # ⬅️ IMPORTANT: Update this!
    MODEL_TYPE = "xlnet" # Or "roberta", "xlmroberta", etc., depending on your trained model
    MODEL_NAME = "xlnet-base-cased" # Or "roberta-base", "xlm-roberta-base", etc.
                                # This should match the base model you used for training.
    print(f"Attempting to load model from: {HUGGING_FACE_MODEL_PATH}")
    labels = ['O',
                'B-Event', 'I-Event', 'E-Event', 'S-Event',
                'B-NonEvent', 'I-NonEvent', 'E-NonEvent', 'S-NonEvent',
                ]
    airdata_file_path = os.path.join('processed', 'airdata', 'corrected_data_step_3.xlsx')
    vto_file_path = os.path.join('processed', 'vto_labs', 'parsed-cleansed.csv')
    vto_lab_input = pd.read_csv(vto_file_path)
    air_data_input = pd.read_excel(airdata_file_path)
    # Load the NER model from Hugging Face.
    # simpletransformers automatically handles downloading and loading.
    # Ensure you specify the correct model_type and model_name that were used during training.
    model = NERModel(
        model_type=MODEL_TYPE,
        model_name=HUGGING_FACE_MODEL_PATH, # Pass the Hugging Face repo ID here
        labels=labels,
        use_cuda=True if torch.cuda.is_available() else False # Use GPU if available
    )
    print("Model loaded successfully!")

    # Preprocess the input raw text using your custom script
    # The 'predict' method expects a list of lists of tokens.
    # Each inner list is a sentence, tokenized.
    air_data_processed = tokenize_test_set(air_data_input['Message'].to_list())

    if not air_data_processed:
        print("Preprocessing resulted in no valid sentences. Cannot perform prediction.")
        return []

    print(f"Preprocessed input for prediction: {air_data_processed}")

    # Perform predictions
    # The result will be a list of lists of dictionaries.
    # Each inner list corresponds to a sentence.
    # Each dictionary contains 'token' and 'entity_group' (or 'label' for older versions).
    output_dir = os.path.join('annotated', 'event-recognition', '')
    predictions, __annotations__ = model.predict(air_data_processed, split_on_space=False)
    airdata_outname = 'airdata-prediction'
    export_predictions_to_conll(predictions, os.path.join(output_dir, f'{airdata_outname}.conll'))
    conll_to_csv(os.path.join(output_dir, f'{airdata_outname}.conll'), os.path.join(output_dir, f'{airdata_outname}.csv'))
    
    vto_lab_processed = tokenize_test_set(vto_lab_input['message'].to_list())
    predictions, __annotations__ = model.predict(vto_lab_processed, split_on_space=False)
    vto_outname = 'vto-lab-prediction'
    export_predictions_to_conll(predictions, os.path.join(output_dir, f'{vto_outname}.conll'))
    conll_to_csv(os.path.join(output_dir, f'{vto_outname}.conll'), os.path.join(output_dir, f'{vto_outname}.csv'))
    
    return 0
    
if __name__ == "__main__":
    main()