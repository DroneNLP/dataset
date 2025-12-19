import os
import csv
import pandas as pd

def findFile(folderName, path_list):
    # os.chdir(folderName)
    item_list = os.listdir(folderName)
    print(item_list)
    # num_folder = 0 
    # for file in item_list:
    #     if (os.path.isdir(file)):
    #         num_folder += 1
    # print(num_folder)
    
    for i, item in enumerate(item_list):
        if os.path.isdir(item):
            print("folder = ", item)
            full = os.path.join(folderName, item)
            print(full)
            findFile(full, path_list)
        else:
            file_ext = item.split(".")        
            file_ext = file_ext[-1] if len(file_ext) > 1 else ""
            if(item.find("extracted_") != -1 and file_ext == "csv"):
                path_list.append(os.path.join(folderName, item))
                # path_list[i] = os.path.join(folderName, item)
    print(path_list)
    return path_list


def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    path_list = []
    for path, subdirs, files in os.walk(dir_path):
        for name in files:
            file_ext = name.split(".")        
            file_ext = file_ext[-1] if len(file_ext) > 1 else ""
            if(name.find("extracted_") != -1 and file_ext == "csv"):
                path_list.append(os.path.join(path, name))
    
    parent_df = pd.DataFrame()
    print(path_list)
    for path in path_list:
        child_df = pd.read_csv(path, encoding='utf-8')
        parent_df = pd.concat([parent_df, child_df])
        
            # print (os.path.join(path, name))
    # empty_list = []
    # path_list = findFile(dir_path, empty_list)
    # parent_df = pd.DataFrame()
    # for path in path_list:
    
    # parent_df.to_csv('parsed.csv', index=False, encoding="utf-8")
    parent_df.to_excel('parsed.xlsx', index=False)


    


if __name__ == "__main__":
    main()