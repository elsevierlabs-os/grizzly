import pandas as pd

def concat(list_of_frames, *args, sort=True, **kwargs):
    return pd.concat(list_of_frames, *args, sort=False, **kwargs).copy_metadata(list_of_frames[0])
