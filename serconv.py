#!/usr/bin/env python3
import sys
import argparse
from io import TextIOWrapper
from typing import Callable, List


def main() -> None:
    fn, args = parse_args(sys.argv[1:])
    maparg(fn, args)


def parse_args(args: List[str]) -> (Callable[[TextIOWrapper], None], List[str]):
    conv_mode = {
        ("json", "yaml"): json2yaml,
        ("yaml", "json"): yaml2json,
        ("json", "toml"): json2toml,
        ("toml", "json"): toml2json,
        ("pickle", "json"): pickle2json,
        ("pickle", "yaml"): pickle2yaml,
        ("pickle", "toml"): pickle2toml,
    }

    format_conv = lambda tup: tup[0] + " -> " + tup[1]

    conv_help = ", ".join(map(format_conv, conv_mode.keys()))

    parser = argparse.ArgumentParser(
        description="Converts serialization formats\n" + conv_help
    )
    parser.add_argument(
        "-f",
        "--from-format",
        help="From format",
        default="toml"
    )
    parser.add_argument(
        "-t",
        "--to",
        help="To format",
        default="json"
    )
    parser.add_argument(
        "FILES",
        nargs="*",
        help="Files to convert, if none given read from stdin and output to stderr"
    )

    opt = parser.parse_args(args)
    mode = (opt.from_format, opt.to)
    try:
        func = conv_mode[mode]
        return func, opt.FILES
    except KeyError:
        print("Illegal conversion:", format_conv(mode), file=sys.stderr)
        exit(1)


def maparg(fn: Callable[[TextIOWrapper], None], args: List[str]) -> None:
    files = []
    try:
        if len(args) == 0:
            files.append(sys.stdin)
        else:
            for fname in args:
                fh = open(fname)
                files.append(fh)
        for f in files:
            fn(f)
    finally:
        for f in files:
            f.close()


def replace_last(s: str, old: str, new: str) -> str:
    (start, _, end) = s.rpartition(old)
    return ''.join([start, new, end])


def convert(deserializer: Callable[[List[str]], dict],
            serializer: Callable[[dict], str],
            base_extensions: List[str],
            new_extension: str,
            fh: TextIOWrapper):
    de = deserializer(fh.read())
    ser = serializer(de)
    if fh == sys.stdin:
        print(ser)
    else:
        name = ""
        for ext in base_extensions:
            if fh.name.endswith(ext):
                name = replace_last(fh.name, ext, new_extension)
                break
        if not name:
            name = fh.name + new_extension
        with open(name, "w") as out:
            out.write(ser)


def yaml_pretty_dump(x: dict) -> str:
    import yaml
    return yaml.dump(x, indent=4, width=80, default_flow_style=False)


def json_pretty_dump(x: dict) -> str:
    import json
    return json.dumps(x, indent=4)


def yaml2json(fh: TextIOWrapper) -> None:
    import yaml
    convert(yaml.load, json_pretty_dump, [".yaml", ".yml"], ".json", fh)


def json2yaml(fh: TextIOWrapper) -> None:
    import json
    convert(json.loads, yaml_pretty_dump, [".json"], ".yml", fh)


def toml2json(fh: TextIOWrapper) -> None:
    import toml
    convert(toml.loads, json_pretty_dump, [".toml"], ".json", fh)


def json2toml(fh: TextIOWrapper) -> None:
    import json, toml
    convert(json.loads, toml.dumps, [".json"], ".toml", fh)


def pickle2json(fh: TextIOWrapper) -> None:
    import pickle
    convert(pickle.loads, json_pretty_dump, [".pickle"], ".json", fh)


def pickle2yaml(fh: TextIOWrapper) -> None:
    import pickle
    convert(pickle.loads, yaml_pretty_dump, [".pickle"], ".yml", fh)


def pickle2toml(fh: TextIOWrapper) -> None:
    import pickle, toml
    convert(pickle.loads, toml.dumps, [".pickle"], ".toml", fh)


if __name__ == '__main__':
    main()
