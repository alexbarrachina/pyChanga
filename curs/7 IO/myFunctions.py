
def get_seq_from_disk(filename):
    f = open(filename)
    big_str = f.read()

    melody = big_str.split(",")
    melody = list(map(int, melody)) # convert strings to ints
    
    print('melody: ', melody)
    return melody