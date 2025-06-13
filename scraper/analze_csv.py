import pandas as pd

def get_max_lengths_with_pandas(csv_path: str):
    df = pd.read_csv(csv_path, dtype=str)      # 全部當字串讀
    # 針對每一欄計算最大長度
    max_lengths = df.apply(lambda col: col.str.len().max())
    return max_lengths.to_dict()

if __name__ == '__main__':
    lengths = get_max_lengths_with_pandas('temp/failed_products.csv')
    for field, length in lengths.items():
        print(f"{field}: {length}")
