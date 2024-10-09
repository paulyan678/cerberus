from argparse import ArgumentParser
from datetime import datetime
from operator import itemgetter
from sys import stdout
from os.path import basename

from jsonlines import open, Writer


def parse_args():
    parser = ArgumentParser(
        prog='confusion',
        description='Evaluate predicted classifications',
        epilog=f'Copyright (c) {datetime.now().year} - Juho Kim',
    )

    parser.add_argument(
        'actual_classifications_pathname',
        help='Actual classifications',
        type=str,
    )
    parser.add_argument(
        'predicted_classifications_pathname',
        help='Predicted classifications',
        type=str,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    with open(args.actual_classifications_pathname) as file:
        actual_classifications = list(file)

    with open(args.predicted_classifications_pathname) as file:
        predicted_classifications = list(file)

    # Extract only the file names from the pathnames
    for row in actual_classifications:
        row['filename'] = basename(row['pathname'])

    for row in predicted_classifications:
        row['filename'] = basename(row['pathname'])

    # Sort based on the file names
    actual_classifications.sort(key=itemgetter('filename'))
    predicted_classifications.sort(key=itemgetter('filename'))

    # Match only based on file names
    filenames = set(map(itemgetter('filename'), actual_classifications))
    predicted_classifications = [
        row
        for row in predicted_classifications
        if row['filename'] in filenames
    ]

    if actual_classifications:
        classes = list(
            map(itemgetter(0), actual_classifications[0]['classifications']),
        )
    else:
        classes = ()

    confusions = []

    for i, class_ in enumerate(classes):
        confusion = {
            'total': 0,
            'actual_positive': 0,
            'actual_negative': 0,
            'predicted_positive': 0,
            'predicted_negative': 0,
            'true_positive': 0,
            'false_positive': 0,
            'true_negative': 0,
            'false_negative': 0,
        }

        for actual, predicted in zip(
                actual_classifications,
                predicted_classifications,
        ):
            actual_classification = actual['classifications'][i][1] is True
            predicted_classification = (
                predicted['classifications'][i][1]
                is True
            )

            confusion['total'] += 1
            confusion['actual_positive'] += actual_classification
            confusion['actual_negative'] += (
                not actual_classification
            )
            confusion['predicted_positive'] += (
                predicted_classification
            )
            confusion['predicted_negative'] += (
                not predicted_classification
            )
            confusion['true_positive'] += (
                actual_classification
                and predicted_classification
            )
            confusion['false_positive'] += (
                not actual_classification
                and predicted_classification
            )
            confusion['false_negative'] += (
                actual_classification
                and not predicted_classification
            )
            confusion['true_negative'] += (
                not actual_classification
                and not predicted_classification
            )

        confusions.append((class_, confusion))

    with Writer(stdout) as writer:
        writer.write_all(confusions)


if __name__ == '__main__':
    main()
