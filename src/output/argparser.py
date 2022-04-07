from argparse import ArgumentParser, ArgumentTypeError


def getargs():
    if hasattr(getargs, "args"):
        return getargs.args

    parser = ArgumentParser(description="Parse the output of COCO JSON.")

    operationgroup = parser.add_mutually_exclusive_group(required=True)
    optionalgroup = parser.add_argument_group()

    operationgroup.add_argument(
        "-d",
        "--decode-rle",
        help="decode the run-length-encoded mask.",
        action="store_true",
    )

    optionalgroup.add_argument(
        "files",
        help="paths to the COCO JSON files.",
        metavar="FILE",
        nargs="+",
    )

    getargs.args = parser.parse_args()

    return getargs.args
