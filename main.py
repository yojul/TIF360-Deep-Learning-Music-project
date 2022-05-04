from datasetBuilder import DatasetBuilder
from miditok import remi
import json

if __name__ == '__main__':
   dataBuilder = DatasetBuilder(path_to_dataset = '.\mozart')
   dataBuilder.generate_json_dataset(seq_length = 8)