from re import compile, IGNORECASE, search
from warnings import warn

DESCRIPTION_PROMPT = 'What is happening in the CCTV footage?'
CLASSIFICATION_PROMPT = '''
Is the CCTV footage of the given class? Begin your response with 'Yes' or 'No'.

CCTV Footage Description: {}

Class: {}
'''.strip()
POSITIVE_PATTERN = compile(r'\byes\b', IGNORECASE)
NEGATIVE_PATTERN = compile(r'\bno\b', IGNORECASE)


def describe(model, video_file):
    try:
        response = model.generate_content([video_file, DESCRIPTION_PROMPT])
        text = response.text
    except Exception as e:  # noqa: E422
        warn(f'Cannot parse text due to error {repr(e)}')

        text = None

    return text


def classify(model, description, classes):
    classifications = []

    for class_ in classes:
        classification = None

        try:
            response = model.generate_content(
                CLASSIFICATION_PROMPT.format(description, class_),
            )
            text = response.text
        except Exception as e:  # noqa: E422
            warn(f'Cannot parse text due to error {repr(e)}')
        else:
            if search(POSITIVE_PATTERN, text):
                classification = True
            elif search(NEGATIVE_PATTERN, text):
                classification = False

        classifications.append([class_, classification])

    return classifications


def describe_and_classify(model, video_file, classes):
    description = describe(model, video_file)
    classifications = classify(model, description, classes)

    return description, classifications
