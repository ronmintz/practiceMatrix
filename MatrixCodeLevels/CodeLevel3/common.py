format = '%Y-%m-%dT%H:%M:%SZ'
merge_period = 30  # number of days to be considered merged promptly

# str_is_number returns True if s is a number, otherwise False.
# Also checks for None: str_is_number(None) = False

def str_is_number(s):
    if s == None:
        return False

    try:
        float(s)
    except ValueError:
        return False

    return True

