import argparse


def parse_args():

    parser = argparse.ArgumentParser(
        description="Preprocess clinical AI evaluation data for one country."
    )

    parser.add_argument(
        "--country",
        required=True,
        help="Country to preprocess, e.g. malawi, kenya, or tanzania.",
    )

    return parser.parse_args()
