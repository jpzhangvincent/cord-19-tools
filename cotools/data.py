import json
import os
from urllib.request import urlopen
import tarfile
import pandas as pd
from typing import Callable, List, Union
from .text import _get_text, _get_abstract, _get_paperid


class Paperset:
    def __init__(self, directory: str) -> None:
        """
        The Paperset class:
            __init__ args:
                directory: a string, the directory where the jsons are stored

            description:
                lazy loader for cord-19 text files. Data is not actually loaded
                until indexing, until then it just indexes files. Can be
                indexed with both ints and slices.
        """
        self.directory = directory
        self.dir_dict = {idx: f for idx, f in enumerate(os.listdir(self.directory))}

    def _load_file(self, path: str) -> dict:
        with open(f"{self.directory}/{path}") as handle:
            outdict = json.loads(handle.read())
        return outdict

    def __getitem__(self, indices: Union[int, slice]) -> Union[list, dict]:
        slicedkeys = list(self.dir_dict.keys())[indices]
        if not isinstance(slicedkeys, list):
            slicedkeys=[slicedkeys]
        out =  [self._load_file(self.dir_dict[key]) for key in slicedkeys]
        if len(out) == 1:
            return out[0]
        else:
            return out

    def apply(self, fn: Callable) -> list:
        return [fn(self._load_file(self.dir_dict[k])) for k in self.dir_dict.keys()]

    def texts(self) -> List[str]:
        return self.apply(_get_text)

    def abstracts(self) -> List[str]:
        return self.apply(_get_abstract)

    def __len__(self) -> int:
        return len(self.dir_dict.keys())

    def get_meta_data(self) -> pd.DataFrame:
        paper_ids = self.apply(_get_paperid)
        all_meta_data_df = pd.read_csv(f"{self.directory}/meta_data.csv")
        paper_meta_data_df = all_meta_data_df[all_meta_data_df.sha.isin(paper_ids)]
        return paper_meta_data_df


def search(ps: Paperset, txt: Union[str, List[str]]) -> List[dict]:
    if type(txt) is not list:
        txt = [txt]
    return [x for x in ps if any(c in _get_text(x).lower() for c in txt) or any (c in _get_abstract(x).lower() for c in txt)]


def download(dir: str='.') -> None:
    data = {
        'comm_use_subset':"https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/2020-03-13/comm_use_subset.tar.gz",
        'noncomm_use_subset':"https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/2020-03-13/noncomm_use_subset.tar.gz",
        'pmc_custom_license':"https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/2020-03-13/pmc_custom_license.tar.gz",
        'biorxiv_medrxiv':"https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/2020-03-13/biorxiv_medrxiv.tar.gz",
        'meta_data':"https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/2020-03-27/metadata.csv"
    }
    if not os.path.exists(dir):
        os.mkdir(dir)
    for d in data.keys():
        handle = urlopen(data[d])
        if d != 'meta_data':
            file_path = f"{dir}/{d}.tar.gz"
        else:
            file_path = f"{dir}/{d}.csv"
        with open(file_path, 'wb') as out:
            while True:
                dat = handle.read(1024)
                if len(dat) == 0: break
                out.write(dat)

    for f in os.listdir(dir):
        if os.path.isdir(f"{dir}/{f}"):
            os.remove(f"{dir}/{f}")
        else:
            if tarfile.is_tarfile(f"{dir}/{f}"):
                tar = tarfile.open(f"{dir}/{f}", 'r:gz')
                tar.extractall(path=dir)
                tar.close()
                os.remove(f"{dir}/{f}")



