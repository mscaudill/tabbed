import string
import re

def make_random_complex_num(rn_generator):
    real_part = rn_generator.uniform(-100000, 100000)
    imag_part = rn_generator.uniform(-100000, 100000)
    num = complex(real_part, imag_part)

    return str(num)
    
def make_random_sci_not_float(rn_generator):
    significand = rn_generator.uniform(-10, 10)
    exponent = rn_generator.randint(-100, 100)
    if (rn_generator.random() > .5):
        return str(significand) + "E" + str(exponent)
    else:
        return str(significand) + "e" + str(exponent)
    
def make_random_integer(rn_generator):
    return str(rn_generator.randint(-100000, 100000))

def make_random_float(rn_generator):
    return str(rn_generator.uniform(-100000, 100000))

def make_random_numeric(rn_generator):

    rand_num = rn_generator.random()
    if (rand_num < 1/3):
        return make_random_integer(rn_generator)
    elif (rand_num < 2/3):
        return make_random_float(rn_generator)
    else:
        return make_random_numeric(rn_generator)
    
def make_random_non_numeric(rn_generator):
    length = rn_generator.randint(1, 20)
    all_chars = string.printable.strip()

    rand_str = "".join(rn_generator.choices(all_chars, k=length))

    non_numeric_insert_pos = rn_generator.randint(0, length+1)

    non_numeric_punctuation = re.sub(r"[.,\+\-]", "", string.punctuation)
    non_numeric_ascii = re.sub(r"[jJeE]", "", string.ascii_letters)
    non_numeric_char = rn_generator.choice(non_numeric_ascii + non_numeric_punctuation)

    # Inserting a non-numeric character always ensures the whole string is non-numeric
    rand_non_numeric = rand_str[:non_numeric_insert_pos] + non_numeric_char + rand_str[non_numeric_insert_pos:]

    return rand_non_numeric

def make_random_string(rn_generator):
    length = rn_generator.randint(0, 30)
    all_chars = string.printable.strip()
    rand_str = "".join(rn_generator.choices(all_chars, k=length))

    return rand_str