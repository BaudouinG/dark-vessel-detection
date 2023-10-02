DATASETS_DIRECTORY_PATH = 'Datasets/'

def getValues(df, orderby='value', descending=True):
    """Return an ordered dictionnary of every distinct value
    and its number of occurrences within any iterable input"""
    temp = dict(df.value_counts(sort=False, dropna=False))
    if orderby == 'value':
        temp = dict(sorted(temp.items(), key=lambda x:x[1], reverse=descending))
    elif orderby == 'key':
        temp = dict(sorted(temp.items(), key=lambda x:x[0], reverse=descending))
    else:
        raise ValueError(f'{orderby} is not a valid argument. Possible values are \'key\' or \'value\'.')
    return temp