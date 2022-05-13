from miditok import get_midi_programs, midi_like, structured, remi, cp_word, octuple_mono, mumidi
from pathlib import Path
from miditoolkit import MidiFile
import random
import json
import os

basic_remi_params = {'Chord': True, 'Rest': True, 'Tempo': True, 'Program': False,
                                 'rest_range': (2, 8),  # (half, 8 beats)
                                 'nb_tempos': 32,  # nb of tempo bins
                                 'tempo_range': (40, 250),  # (min, max)
                                 # ----------------------
                                 'TimeSignature': False,
                                 'time_signature_range': (4, 1)}

class DatasetBuilder() :
    def __init__(self,path_to_dataset, tokenizer = 'REMI', output_directory = r'.\\dataset\\' , param = basic_remi_params):
        self.paths = list(Path(path_to_dataset).glob('**/*.mid'))
        self.output_path = output_directory
        self.seq_counter = 0
        # Default Parameters
        pitch_range = range(21, 109)
        beat_res = {(0, 4): 8, (4, 12): 4}
        nb_velocities = 32
        additional_tokens = param
        token_dict = { 'REMI' : remi.REMI(pitch_range, beat_res, nb_velocities, additional_tokens),
                            'MIDILike' : midi_like.MIDILike(pitch_range, beat_res, nb_velocities, additional_tokens),
                            'CPWord' : cp_word.CPWord(pitch_range, beat_res, nb_velocities, additional_tokens),
                            'Octuple' : octuple_mono.OctupleMono(pitch_range, beat_res, nb_velocities, additional_tokens),
                            'MuMIDI' : mumidi.MuMIDI(pitch_range, beat_res, nb_velocities, additional_tokens),
                            'Structured' : structured.Structured(pitch_range, beat_res, nb_velocities, additional_tokens)}
        self.tokenizer = token_dict[tokenizer]


    def tokenize_all(self) :
        '''
        Create a list with all token from the specified directory
        :return: a list of token for all midi files
        '''
        token_dataset = []

        def midi_valid(midi) -> bool:
            if any(ts.numerator != 4 for ts in midi.time_signature_changes):
                return False  # time signature different from 4/*, 4 beats per bar
            if midi.max_tick < 10 * midi.ticks_per_beat:
                return False  # this MIDI is too short
            return True

        for fn in self.paths :
            midi = MidiFile(fn)
            if midi_valid(midi) :
                token_dataset.append(self.tokenizer.midi_to_tokens(midi))
        return(token_dataset)


    def split_token(self,token, seq_length = 8) :
        '''
        :param token: Midi token with several tracks (2 for a piano midi)
        :param seq_length: Desired length in bars for the split
        :return: splitted token list
        '''
        tok_list = { i : [] for i in range(len(token))}
        for t,track in enumerate(token) :
            bar_count = -1
            last_seq_idx = 0
            for i,event in enumerate(track) :
                if event == 1 :
                    bar_count +=1
                    if bar_count == seq_length :
                        tok_list[t].append(track[last_seq_idx : i-1])
                        bar_count = 0
                        last_seq_idx = i
        self.seq_counter += len(tok_list[0])
        return(tok_list)

    def write_json(self,token):
        '''
        write the data as json - as dict with voice 0 and 1, splitted in seq_length bars sequences
        :param token:
        :return:
        '''
        #now = datetime.now().strftime("%H%M%S")
        r = random.randint(0,1000000)
        with open(self.output_path + f'dataset_{str(r)}.json' , 'w') as f :
            json.dump(token,f)

    def generate_json_dataset(self, seq_length = 8):
        '''
        generate json file for all valid (4/4) midi files in the specified directory
        :param seq_length: sequence length in bars
        :return:
        '''
        dataset = self.tokenize_all()
        for tok in dataset :
            tok_bars = self.split_token(tok,seq_length = seq_length)
            self.write_json(tok_bars)




def merge_and_process_data(path_to_directory = r'.\\dataset\\') :
    dataset = []
    for dirname, _, filenames in os.walk(path_to_directory):
        for filename in filenames:
            print(os.path.join(dirname, filename))
            with open(os.path.join(dirname, filename)) as f:
                dataset.append(json.load(f))
    processed_data = []
    for piece in dataset:
        if len(piece['0']) == len(piece['1']):  # Keep only pieces where both voices have the same length
            [processed_data.append([piece['0'][i], piece['1'][i]]) for i in
             range(len(piece['0']))]  # Add [voice 1, voice 2] for every 8 bars sequences
    print(' %s sequences in the dataset' % len(processed_data))
    print('The longest sequence contains %s tokens' % max([ max([len(i) for i in d]) for d in processed_data]))

    return(processed_data)
if __name__ == '__main__':
    pass