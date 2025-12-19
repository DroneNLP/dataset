import os
import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src_dir", default="src/evidence/decrypted", help="Folder with decrypted logs")
    parser.add_argument("--dst_dir", default="src/evidence/parsed", help="Folder to save parsed output")
    args = parser.parse_args()

    os.makedirs(args.dst_dir, exist_ok=True)
    
    files = os.listdir(args.src_dir)
    files = [file for file in files if os.path.splitext(file)[1] == '.csv' ]
    file_count = 1
    for file in files:
        date = []
        time = []
        message_type = []
        message = []
        file_df = pd.read_csv(os.path.join(args.src_dir, file), skiprows=1) # since the first row contains sep=,
        timeline_df = file_df[['CUSTOM.date [local]', 'CUSTOM.updateTime [local]', 'APP.tip', 'APP.warning']]
        for i, row in timeline_df.iterrows():
            if not pd.isna(row['APP.tip']):
                date.append(row['CUSTOM.date [local]'])
                time.append(row['CUSTOM.updateTime [local]'])
                message_type.append('tip')
                message.append(row['APP.tip'])
            if not pd.isna(row['APP.warning']):
                date.append(row['CUSTOM.date [local]'])
                time.append(row['CUSTOM.updateTime [local]'])
                message_type.append('warning')
                message.append(row['APP.warning'])
        parsed_df = pd.DataFrame({
            'date': date,
            'time': time,
            'message_type': message_type,
            'message': message
        })

        parsed_df.to_excel(os.path.join(args.dst_dir, f'flight_log_{file_count}' + '.xlsx'), index=False)
        file_count += 1

if __name__ == "__main__":
    main()