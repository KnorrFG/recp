"""A command line tool to copy files based on regular expressions."""
__version__ = "1.0.1"

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, NamedTuple

import click
import pandas as pd
from tqdm import tqdm


class REError(Exception): pass


class Mapper:
    def __init__(self, table: pd.DataFrame = None, mappings: str = None):
        self.table = table
        if mappings:
            self.mappings = dict([x.strip() for x in mapping.split("->")] 
                                 for mapping in mappings.split(";"))

    def __call__(self, attrs: dict)-> dict:
        if self.table is None:
            return attrs

        is_in_mappings = (key in self.mappings for key in attrs)
        new_keys = (key if not is_mapped else self.mappings[key] 
                    for key, is_mapped in zip(attrs, is_in_mappings))
        return {new_key: val if new_key == old_key else 
                        self.table[self.table[old_key] == val][new_key].values[0]
                for (old_key, val), new_key in zip(attrs.items(), new_keys)}

class PathDescription(NamedTuple):
    path: Path
    attrs: dict

def walk_re_path(current_path: Path, path_elems: List[str], 
                 is_re: List[bool], res: List[re.Match], 
                 fail_silently: bool = False,
                 current_group_dict: dict = None):
    cgd = current_group_dict or {}
    if is_re[0]:
        for dc in current_path.iterdir():
            match = res[0].match(dc.name)
            if match:
                next_group_dict = dict(**cgd, **match.groupdict())
                if len(path_elems) > 1:
                    yield from walk_re_path(dc, path_elems[1:], is_re[1:], 
                                            res[1:], fail_silently, 
                                            next_group_dict)
                else: yield PathDescription(dc, next_group_dict)
    else:
        new_path = current_path / path_elems[0]
        if not new_path.exists():
            if fail_silently:
                yield None
            else:
                raise REError(f"The path {str(new_path)} does not exist")
        elif len(path_elems) > 1: 
            yield from walk_re_path(new_path, path_elems[1:], is_re[1:], 
                                      res[1:], fail_silently, cgd)
        else:
            yield PathDescription(new_path, cgd)


def contains_regex(elem: str):
    return re.search(r"[^a-zA-Z_\d.~]", elem) is not None


def to_abs(path: str):
    stripped_path = path.strip()
    if stripped_path[0] =="~":
        return str(Path.home()) + stripped_path[1:]
    elif stripped_path.startswith(".."):
        return str(Path.pwd().parent) + stripped_path[2:]
    elif stripped_path[0] == ".":
        return str(Path.cwd()) + stripped_path[1:]
    else:
        return stripped_path


@click.command()
@click.argument("src-regex")
@click.argument("target-format-str")
@click.option("--copy", "-c", is_flag=True, 
    help="actually copy the files")
@click.option("--mapping-file", "-f", 
    help="csv file that contains mappings")
@click.option("--mapping-str", "-s", 
    help="String of format var1_old->var1_new[;var2_old->var2_new[;...]]")
@click.option("--fail-silently", "-q", is_flag=True,
    help="if a subpath that should exist does not exist, ignore it")
@click.option("--first-n", "-n", type=int, default=1,
    help="defines how many examples should be printed")
@click.option("--skip-existing", "-e", is_flag=True,
    help="skip file if target already exists")
def main(src_regex: str, target_format_str: str, copy: bool, 
         mapping_file: str, mapping_str: str, fail_silently: bool,
         first_n: int, skip_existing: bool):
    """Coppies all files that match a regular expression of a source path 
       to a target path, which can be defined using the names of named capture 
       groups from the source regex. Only Unix-paths are supported.

       If the source regex describes a file, the target format string must to.
       It is file to file or folder to folder. In the second case the target
       folder must not exist (unless you used --skip-existing)

       Since writing a regular expression is nearly always an iterative process
       by default no coppying will be done, and only a preview will be displayed.
       -n determines how many examples are shown. To copy the files use -c.
       
       Every folder name and the file name are individually tested for being 
       regulare expressions and a dot will be interpreted as normal dot, unless
       any other sign of a regular expression is found, in which case the dot
       will be interpreted as part of it.
       
       It is possible to pass a mapping string with -s to map the value of a
       capture group to something else. If a mapping string is given, also a 
       mapping file must be given, which should be a pandas friendly csv (i.e. 
       will be correctly loaded by pandas with default parameters)
       If a mapping file and a mapping string are given the value of the mapped
       variable will be replaced according to the table in the csv file"""
    try:
        path_elems = to_abs(src_regex).split("/")
        target_format_str = to_abs(target_format_str)
        is_re = [contains_regex(e) for e in path_elems]
        res = [re.compile(e) if reg else None
               for e, reg in zip(path_elems, is_re)]

        if bool(mapping_str) != bool(mapping_file):
            raise REError("Either --maping-str and --mapping-file must be "
                          "given, or none of it")
        
        mapper = Mapper(pd.read_csv(mapping_file, dtype=object), mapping_str)\
            if mapping_str else Mapper()
        copy_ops = [(pd.path, target_format_str.format(**mapper(pd.attrs))) 
                    for pd in walk_re_path(Path("/"), path_elems, 
                                          is_re, res, fail_silently)
                    if pd is not None]
        if not copy:
            print(f"{len(copy_ops)} files found.")
            print("To copy the files use -c")
            for source, target in copy_ops[:first_n]:
                print(f"{source} -> {target}")
        else:
            for path, target in tqdm(copy_ops):
                target_path = Path(target)
                if not (skip_existing and target_path.exists()):
                    if path.is_dir():
                        shutil.copytree(path, target)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(path, target)

    except REError as e:
        print(e)


if __name__ == "__main__":
    main()
